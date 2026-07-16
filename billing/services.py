"""Moteur de facturation automatique SGHL."""

from decimal import Decimal
from datetime import date, timedelta

from django.db import transaction, models
from django.utils import timezone

from clinical.models import Patient, Admission, Consultation
from laboratory.models import DemandeExamen
from prescriptions.models import Prescription
from .models import (
    Facture, LigneFacture, PriseEnChargeAssurance,
    JournalComptable, BillingError,
)

TARIF_CONSULTATION = Decimal('15000')
TARIF_NUITEE_DEFAUT = Decimal('25000')


def serialiser_facture(facture):
    lignes = [
        {
            "id": l.id,
            "type_ligne": l.type_ligne,
            "description": l.description,
            "quantite": l.quantite,
            "prix_unitaire": float(l.prix_unitaire),
            "montant": float(l.montant),
        }
        for l in facture.lignes.all()
    ]
    return {
        "id": facture.id,
        "numero_facture": facture.numero_facture,
        "patient_id": facture.patient_id,
        "patient_nom": f"{facture.patient.nom} {facture.patient.prenom}",
        "admission_id": facture.admission_id,
        "statut": facture.statut,
        "sous_total": float(facture.sous_total),
        "remise": float(facture.remise),
        "montant_assurance": float(facture.montant_assurance),
        "montant_patient": float(facture.montant_patient),
        "montant_paye": float(facture.montant_paye),
        "montant_restant": float(facture.montant_restant),
        "date_emission": facture.date_emission.isoformat(),
        "pdf_disponible": bool(facture.fichier_pdf),
        "lignes": lignes,
        "nb_lignes": len(lignes),
    }


def _calculer_nuitees(admission):
    fin = admission.date_sortie or timezone.now()
    nuits = max(1, (fin.date() - admission.date_entree.date()).days)
    if admission.lit_id:
        prix = admission.lit.chambre.prix_par_jour or TARIF_NUITEE_DEFAUT
        chambre = admission.lit.chambre.numero
        service = admission.service.nom
    else:
        prix = TARIF_NUITEE_DEFAUT
        chambre = 'N/A'
        service = admission.service.nom
    return {
        "type_ligne": "NUITEE",
        "description": f"Hébergement {service} — Chambre {chambre} ({nuits} nuit(s))",
        "quantite": nuits,
        "prix_unitaire": prix,
        "admission": admission,
    }


def _collecter_consultations(patient, admission):
    qs = Consultation.objects.filter(patient=patient)
    if admission:
        qs = qs.filter(
            models.Q(admission=admission)
            | models.Q(
                date_consultation__gte=admission.date_entree,
                date_consultation__lte=admission.date_sortie or timezone.now(),
            )
        )
    return [
        {
            "type_ligne": "CONSULTATION",
            "description": f"Consultation — {c.service.nom} — Dr {c.medecin.get_full_name()}",
            "quantite": 1,
            "prix_unitaire": TARIF_CONSULTATION,
            "admission": admission,
        }
        for c in qs.select_related('medecin', 'service')
    ]


def _collecter_examens(patient, admission):
    qs = DemandeExamen.objects.filter(patient=patient, statut='VALIDE')
    if admission:
        qs = qs.filter(date_prescription__gte=admission.date_entree)
    return [
        {
            "type_ligne": "EXAMEN",
            "description": f"Examen labo — {d.examen_type.nom}",
            "quantite": 1,
            "prix_unitaire": d.examen_type.prix,
            "demande_examen": d,
            "admission": admission,
        }
        for d in qs.select_related('examen_type')
    ]


def _collecter_medicaments(patient, admission):
    qs = Prescription.objects.filter(patient=patient, est_verrouillee=True)
    if admission:
        qs = qs.filter(date_prescription__gte=admission.date_entree)
    lignes = []
    for presc in qs.prefetch_related('lignes__medicament'):
        for lp in presc.lignes.all():
            lignes.append({
                "type_ligne": "MEDICAMENT",
                "description": f"{lp.medicament.nom} ({lp.medicament.dosage})",
                "quantite": lp.quantite_prescitee,
                "prix_unitaire": lp.medicament.prix_unitaire,
                "prescription": presc,
                "admission": admission,
            })
    return lignes


@transaction.atomic
def generer_facture_automatique(patient_id, admission_id, emise_par_id):
    """Génère une facture brouillon : nuitées, consultations, examens, médicaments."""
    patient = Patient.objects.get(id=patient_id)
    admission = None

    if admission_id:
        admission = Admission.objects.select_related(
            'service', 'lit__chambre',
        ).get(id=admission_id, patient=patient)

        existante = Facture.objects.filter(admission=admission, statut='BROUILLON').first()
        if existante:
            raise BillingError(
                f"Une facture brouillon existe déjà : {existante.numero_facture}"
            )

    facture = Facture.objects.create(
        patient=patient,
        admission=admission,
        emise_par_id=emise_par_id,
        statut='BROUILLON',
    )

    items = []
    if admission:
        items.append(_calculer_nuitees(admission))
    items.extend(_collecter_consultations(patient, admission))
    items.extend(_collecter_examens(patient, admission))
    items.extend(_collecter_medicaments(patient, admission))

    if not items:
        raise BillingError("Aucun élément facturable trouvé pour ce patient/admission")

    for item in items:
        LigneFacture.objects.create(
            facture=facture,
            type_ligne=item["type_ligne"],
            description=item["description"],
            quantite=item["quantite"],
            prix_unitaire=item["prix_unitaire"],
            prescription=item.get("prescription"),
            demande_examen=item.get("demande_examen"),
            admission=item.get("admission"),
        )

    facture.recalculer_montants()
    return facture


@transaction.atomic
def appliquer_tiers_payant(facture_id):
    """Applique le tiers-payant assurance sur une facture brouillon."""
    facture = Facture.objects.select_for_update().get(id=facture_id)

    if facture.statut != 'BROUILLON':
        raise BillingError("Le tiers-payant ne s'applique qu'aux factures brouillon")

    today = date.today()
    prise = PriseEnChargeAssurance.objects.filter(
        patient=facture.patient,
        est_active=True,
        date_debut__lte=today,
        date_fin__gte=today,
    ).select_related('assurance').first()

    if not prise:
        facture.montant_assurance = Decimal('0')
        facture.recalculer_montants()
        return facture, None

    montant_apres_remise = facture.sous_total - facture.remise
    taux = Decimal(prise.assurance.taux_prise_en_charge) / Decimal('100')
    facture.montant_assurance = (montant_apres_remise * taux).quantize(Decimal('0.01'))
    facture.notes = (
        f"{facture.notes}\nTiers-payant : {prise.assurance.nom} "
        f"({prise.assurance.taux_prise_en_charge}%) — Contrat {prise.numero_contrat}"
    ).strip()
    facture.recalculer_montants()
    return facture, prise


@transaction.atomic
def emettre_facture(facture_id, utilisateur_id):
    """Émet la facture, génère le PDF et enregistre le journal comptable."""
    from authentication.models import Utilisateur
    from .pdf_generator import generer_facture_pdf

    facture = Facture.objects.select_for_update().select_related(
        'patient', 'admission',
    ).prefetch_related('lignes').get(id=facture_id)

    if facture.statut != 'BROUILLON':
        raise BillingError("Seules les factures brouillon peuvent être émises")
    if not facture.lignes.exists():
        raise BillingError("Facture sans lignes")

    utilisateur = Utilisateur.objects.get(id=utilisateur_id)

    facture.statut = 'EMISE'
    facture.date_echeance = date.today() + timedelta(days=30)

    pdf_path = generer_facture_pdf(facture)
    facture.fichier_pdf = pdf_path
    facture.save()

    JournalComptable.enregistrer(
        facture=facture,
        type_operation='EMISSION',
        montant=facture.sous_total - facture.remise,
        description=f"Émission facture {facture.numero_facture} — {facture.patient}",
        utilisateur=utilisateur,
    )

    if facture.montant_assurance > 0:
        JournalComptable.enregistrer(
            facture=facture,
            type_operation='TIERS_PAYANT',
            montant=facture.montant_assurance,
            description=f"Tiers-payant assurance — {facture.numero_facture}",
            utilisateur=utilisateur,
        )

    facture.recalculer_montants()
    return facture
