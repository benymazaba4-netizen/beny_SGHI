from django.db import transaction, models
from django.utils import timezone

from authentication.models import Utilisateur
from pharmacy.services import decrementer_stock, verifier_stock_disponible, StockError
from .models import (
    Prescription, LignePrescription, AlerteDoseOmise,
    PrescriptionError,
)


def serialiser_prescription(prescription):
    lignes = [
        {
            "id": l.id,
            "medicament_id": l.medicament_id,
            "medicament_nom": l.medicament.nom,
            "medicament_code": l.medicament.code,
            "quantite_prescitee": l.quantite_prescitee,
            "quantite_administree": l.quantite_administree,
            "quantite_restante": l.quantite_restante(),
            "frequence": l.frequence,
            "duree_jours": l.duree_jours,
            "doses_omises": l.doses_omises,
        }
        for l in prescription.lignes.select_related('medicament')
    ]
    return {
        "id": prescription.id,
        "patient_id": prescription.patient_id,
        "patient_nom": f"{prescription.patient.nom} {prescription.patient.prenom}",
        "medecin_id": prescription.medecin_id,
        "medecin": prescription.medecin.get_full_name(),
        "consultation_id": prescription.consultation_id,
        "statut": prescription.statut,
        "est_verrouillee": prescription.est_verrouillee,
        "date_prescription": prescription.date_prescription.isoformat(),
        "date_debut": str(prescription.date_debut),
        "date_fin": str(prescription.date_fin) if prescription.date_fin else None,
        "date_validation": prescription.date_validation.isoformat() if prescription.date_validation else None,
        "instructions": prescription.instructions,
        "signature_electronique": prescription.signature_electronique,
        "lignes": lignes,
        "nb_lignes": len(lignes),
    }


@transaction.atomic
def valider_prescription(prescription_id, validateur_id):
    """
    Valide et verrouille une prescription.
    Décrémente automatiquement les stocks pharmacie (FIFO).
    """
    prescription = Prescription.objects.select_for_update().select_related(
        'patient', 'medecin',
    ).prefetch_related('lignes__medicament').get(id=prescription_id)

    if prescription.est_verrouillee:
        raise PrescriptionError("Prescription déjà verrouillée")

    lignes = list(prescription.lignes.all())
    if not lignes:
        raise PrescriptionError("Impossible de valider une prescription sans lignes")

    for ligne in lignes:
        verifier_stock_disponible(ligne.medicament_id, ligne.quantite_prescitee)

    validateur = Utilisateur.objects.get(id=validateur_id)
    mouvements = []

    for ligne in lignes:
        mvt = decrementer_stock(
            medicament_id=ligne.medicament_id,
            quantite=ligne.quantite_prescitee,
            utilisateur_id=validateur_id,
            reference=f"PRESC-{prescription.id}",
            commentaire=f"Validation prescription #{prescription.id} — {ligne.medicament.nom}",
        )
        mouvements.extend(mvt)

    if not prescription.date_fin:
        from datetime import timedelta
        max_duree = max(l.duree_jours for l in lignes)
        prescription.date_fin = prescription.date_debut + timedelta(days=max_duree)

    prescription.verrouiller(validateur)
    return prescription, mouvements


@transaction.atomic
def enregistrer_dose_omise(ligne_id, infirmier_id, commentaire=''):
    """Enregistre une dose omise et crée une alerte."""
    ligne = LignePrescription.objects.select_for_update().select_related(
        'prescription', 'medicament',
    ).get(id=ligne_id)

    if not ligne.prescription.est_verrouillee:
        raise PrescriptionError("Prescription non validée")
    if ligne.est_entièrement_administree():
        raise PrescriptionError("Toutes les doses ont déjà été administrées")

    ligne.doses_omises += 1
    ligne.save(update_fields=['doses_omises'])

    message = (
        f"Dose omise — {ligne.medicament.nom} "
        f"(prescription #{ligne.prescription_id}, "
        f"{ligne.doses_omises} dose(s) omise(s) au total)"
    )
    if commentaire:
        message += f" — {commentaire}"

    alerte = AlerteDoseOmise.objects.create(
        ligne_prescription=ligne,
        message=message,
    )
    return ligne, alerte


def lister_alertes_doses():
    """Retourne les alertes de doses omises non traitées + lignes en retard."""
    alertes = AlerteDoseOmise.objects.filter(
        est_traitee=False,
    ).select_related(
        'ligne_prescription__medicament',
        'ligne_prescription__prescription__patient',
    )

    resultat = [
        {
            "id": a.id,
            "type": "DOSE_OMISE",
            "message": a.message,
            "date_alerte": a.date_alerte.isoformat(),
            "prescription_id": a.ligne_prescription.prescription_id,
            "patient": str(a.ligne_prescription.prescription.patient),
            "medicament": a.ligne_prescription.medicament.nom,
        }
        for a in alertes
    ]

    today = timezone.now().date()
    lignes_en_retard = LignePrescription.objects.filter(
        prescription__est_verrouillee=True,
        prescription__statut__in=['VALIDE', 'PARTIELLE'],
        quantite_administree__lt=models.F('quantite_prescitee'),
        prescription__date_fin__lt=today,
    ).select_related('medicament', 'prescription__patient')

    for ligne in lignes_en_retard:
        if not any(r['prescription_id'] == ligne.prescription_id for r in resultat):
            resultat.append({
                "id": None,
                "type": "RETARD_TRAITEMENT",
                "message": (
                    f"Traitement en retard — {ligne.medicament.nom} "
                    f"({ligne.quantite_restante()} dose(s) restante(s))"
                ),
                "date_alerte": today.isoformat(),
                "prescription_id": ligne.prescription_id,
                "patient": str(ligne.prescription.patient),
                "medicament": ligne.medicament.nom,
            })

    return resultat
