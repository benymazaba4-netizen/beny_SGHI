from django.db import transaction
from django.utils import timezone

from authentication.models import Utilisateur
from common.db_concurrency import get_locked, lock_for_update
from .models import (
    DemandeExamen, Prelevement, ResultatExamen,
    HistoriqueModificationResultat, LISError,
)


LIS_WORKFLOW_STEPS = (
    {'code': 'PRESCRIT', 'label': 'Commande', 'description': 'Examen prescrit par le médecin'},
    {'code': 'PRELEVE', 'label': 'Prélèvement', 'description': 'Échantillon collecté et tracé'},
    {'code': 'EN_COURS', 'label': 'Affectation', 'description': 'Dossier affecté au biologiste'},
    {'code': 'VALIDATION', 'label': 'Saisie résultats', 'description': 'Résultats saisis, validation requise'},
    {'code': 'VALIDE', 'label': 'Validation', 'description': 'Résultat validé par biologiste'},
    {'code': 'PUBLIE', 'label': 'Publication', 'description': 'Compte rendu disponible au dossier'},
)


def workflow_lis(statut: str, resultat=None) -> list[dict]:
    if resultat and getattr(resultat, 'est_publie', False):
        current_index = len(LIS_WORKFLOW_STEPS) - 1
    elif statut == 'VALIDE':
        current_index = 4
    else:
        order = [step['code'] for step in LIS_WORKFLOW_STEPS]
        current_index = order.index(statut) if statut in order else 0
    steps = []
    for index, step in enumerate(LIS_WORKFLOW_STEPS):
        state = 'done' if index < current_index else 'current' if index == current_index else 'pending'
        steps.append({**step, 'state': state})
    return steps


def serialiser_demande(demande):
    resultat = getattr(demande, 'resultat', None)
    return {
        "id": demande.id,
        "patient_id": demande.patient_id,
        "patient_nom": demande.patient.nom,
        "patient_prenom": demande.patient.prenom,
        "numero_dossier": demande.patient.numero_dossier,
        "examen_type_id": demande.examen_type_id,
        "examen_type_nom": demande.examen_type.nom,
        "examen_type_code": demande.examen_type.code,
        "statut": demande.statut,
        "urgence": demande.urgence,
        "date_prescription": demande.date_prescription.isoformat(),
        "date_prelevement": demande.date_prelevement.isoformat() if demande.date_prelevement else None,
        "date_affectation": demande.date_affectation.isoformat() if demande.date_affectation else None,
        "date_validation": demande.date_validation.isoformat() if demande.date_validation else None,
        "date_publication": demande.date_publication.isoformat() if demande.date_publication else None,
        "medecin_prescripteur": demande.medecin_prescripteur.get_full_name(),
        "affecte_a": demande.affecte_a.get_full_name() if demande.affecte_a else None,
        "valide_par": demande.valide_par.get_full_name() if demande.valide_par else None,
        "notes_prescripteur": demande.notes_prescripteur,
        "a_resultat": bool(resultat),
        "resultat_id": resultat.id if resultat else None,
        "resultat_valide": resultat.est_valide if resultat else False,
        "resultat_publie": resultat.est_publie if resultat else False,
        "resultats": resultat.resultats if resultat else '',
        "interpretation": resultat.interpretation if resultat else '',
        "workflow": workflow_lis(demande.statut, resultat),
    }


def serialiser_resultat(resultat):
    return {
        "id": resultat.id,
        "demande_id": resultat.demande_id,
        "resultats": resultat.resultats,
        "interpretation": resultat.interpretation,
        "est_valide": resultat.est_valide,
        "est_publie": resultat.est_publie,
        "date_saisie": resultat.date_saisie.isoformat(),
        "date_validation": resultat.date_validation.isoformat() if resultat.date_validation else None,
        "saisie_par": resultat.saisie_par.get_full_name() if resultat.saisie_par else None,
        "valide_par": resultat.valide_par.get_full_name() if resultat.valide_par else None,
        "signature_electronique": resultat.signature_electronique,
        "pdf_disponible": bool(resultat.fichier_pdf),
    }


@transaction.atomic
def creer_demande(patient_id, medecin_prescripteur_id, consultation_id, examen_type_id,
                  urgence=False, notes_prescripteur=''):
    """Crée une demande d'examen avec verrouillage consultation (workflow LIS)."""
    from clinical.models import Consultation, Patient

    patient = get_locked(Patient, id=patient_id)
    consultation = get_locked(Consultation, id=consultation_id)

    if consultation.patient_id != patient.id:
        raise LISError("La consultation n'appartient pas au patient indiqué")

    if consultation.medecin_id != medecin_prescripteur_id:
        raise LISError("Le médecin prescripteur ne correspond pas à la consultation")

    demande = DemandeExamen.objects.create(
        patient=patient,
        consultation=consultation,
        examen_type_id=examen_type_id,
        medecin_prescripteur_id=medecin_prescripteur_id,
        urgence=urgence,
        notes_prescripteur=notes_prescripteur,
        statut='PRESCRIT',
    )
    return DemandeExamen.objects.select_related(
        'patient', 'examen_type', 'medecin_prescripteur',
    ).get(pk=demande.pk)


@transaction.atomic
def enregistrer_prelevement(demande_id, user_id, data):
    demande = get_locked(DemandeExamen, id=demande_id)

    if demande.statut != 'PRESCRIT':
        raise LISError(f"Prélèvement impossible — statut actuel : {demande.statut}")
    if hasattr(demande, 'prelevement'):
        raise LISError("Un prélèvement existe déjà pour cette demande")

    prelevement = Prelevement.objects.create(
        demande=demande,
        preleve_par_id=user_id,
        **data,
    )
    demande.transitionner('PRELEVE')
    demande.date_prelevement = prelevement.date_prelevement
    demande.preleve_par_id = user_id
    demande.save(update_fields=['date_prelevement', 'preleve_par'])
    return prelevement


@transaction.atomic
def affecter_demande(demande_id, biologiste_id):
    demande = get_locked(DemandeExamen, id=demande_id)

    if demande.statut != 'PRELEVE':
        raise LISError(f"Affectation impossible — statut actuel : {demande.statut}")

    biologiste = Utilisateur.objects.get(id=biologiste_id, role='BIOLOGISTE')

    demande.transitionner('EN_COURS')
    demande.affecte_a = biologiste
    demande.date_affectation = timezone.now()
    demande.save(update_fields=['affecte_a', 'date_affectation'])
    return demande


@transaction.atomic
def saisir_resultat(demande_id, user_id, resultats, interpretation=''):
    demande = get_locked(DemandeExamen, id=demande_id)

    if demande.statut != 'EN_COURS':
        raise LISError(f"Saisie impossible — statut actuel : {demande.statut}")
    if hasattr(demande, 'resultat'):
        raise LISError("Un résultat existe déjà — utilisez la modification")

    resultat = ResultatExamen.objects.create(
        demande=demande,
        resultats=resultats,
        interpretation=interpretation,
        saisie_par_id=user_id,
    )
    demande.transitionner('VALIDATION')
    return resultat


@transaction.atomic
def modifier_resultat(resultat_id, user_id, resultats, interpretation='', request=None):
    resultat = get_locked(ResultatExamen, id=resultat_id)

    if resultat.est_valide:
        raise PermissionError("Résultat validé — modification interdite (immuabilité)")

    utilisateur = Utilisateur.objects.get(id=user_id)
    if not resultat.peut_modifier(utilisateur):
        raise PermissionError("Vous n'êtes pas autorisé à modifier ce résultat")

    anciens_resultats = resultat.resultats
    ancienne_interpretation = resultat.interpretation

    HistoriqueModificationResultat.objects.create(
        resultat=resultat,
        modifie_par_id=user_id,
        anciens_resultats=anciens_resultats,
        nouveaux_resultats=resultats,
        ancienne_interpretation=ancienne_interpretation,
        nouvelle_interpretation=interpretation,
        ip_adresse=request.META.get('REMOTE_ADDR') if request else None,
    )

    resultat.resultats = resultats
    resultat.interpretation = interpretation
    resultat.save()
    return resultat


@transaction.atomic
def valider_et_publier(resultat_id, biologiste_id):
    """Validation biologiste + génération PDF + publication."""
    from .pdf_generator import generer_compte_rendu_pdf

    resultat = lock_for_update(ResultatExamen.objects).select_related(
        'demande__patient', 'demande__examen_type',
    ).get(id=resultat_id)
    biologiste = Utilisateur.objects.get(id=biologiste_id)
    if biologiste.role != 'BIOLOGISTE':
        raise PermissionError("Seul un biologiste peut valider un résultat")

    resultat.valider(biologiste)

    pdf_path = generer_compte_rendu_pdf(resultat)
    resultat.fichier_pdf = pdf_path
    resultat.save(update_fields=['fichier_pdf'])

    resultat.publier()
    from common.email_utils import notify_exam_published
    notify_exam_published(resultat.demande.patient, resultat.demande.examen_type.nom)
    return resultat
