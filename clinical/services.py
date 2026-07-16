from django.db import transaction, IntegrityError

from clinical.models import Admission, Patient
from hospital_structure.models import Lit, ServiceHospitalier
from common.db_concurrency import lock_for_update, get_locked


class HospitalisationError(Exception):
    pass


def _verifier_admission_active(admission):
    if not admission.est_active:
        raise HospitalisationError("Aucune hospitalisation active")


@transaction.atomic
def creer_admission(
    patient_id,
    service_id,
    lit_id,
    medecin_referent_id,
    motif_hospitalisation,
    date_previsionnelle_sortie,
    type_admission='PROGRAMMEE',
    lit_version=None,
):
    """Crée une admission en vérifiant la disponibilité du lit (1 lit = 1 patient)."""
    patient = get_locked(Patient, id=patient_id)

    if Admission.objects.filter(patient=patient, statut='EN_COURS').exists():
        raise HospitalisationError("Ce patient a déjà une hospitalisation en cours")

    service = ServiceHospitalier.objects.get(id=service_id, est_actif=True)
    lit = get_locked(Lit, id=lit_id)

    if lit.chambre.service_id != service_id:
        raise HospitalisationError("Le lit sélectionné n'appartient pas au service choisi")

    if not lit.chambre.est_actif:
        raise HospitalisationError("La chambre associée au lit est inactive")

    if lit.statut == 'HORS_SERVICE':
        raise HospitalisationError(f"Le lit {lit.numero} est hors service")

    if not lit.est_libre():
        raise HospitalisationError(f"Le lit {lit.numero} n'est pas disponible")

    if Admission.objects.filter(lit=lit, statut='EN_COURS').exists():
        raise HospitalisationError(f"Le lit {lit.numero} est déjà occupé par une admission active")

    try:
        lit.occuper_atomique(patient, version_attendue=lit_version)
    except ValueError as exc:
        raise HospitalisationError(str(exc)) from exc

    try:
        admission = Admission.objects.create(
            patient=patient,
            service=service,
            lit=lit,
            medecin_referent_id=medecin_referent_id,
            motif_hospitalisation=motif_hospitalisation,
            date_previsionnelle_sortie=date_previsionnelle_sortie,
            type_admission=type_admission,
            statut='EN_COURS',
        )
    except IntegrityError as exc:
        try:
            lit.liberer_atomique()
        except ValueError:
            pass
        raise HospitalisationError(
            f"Le lit {lit.numero} vient d'être occupé (concurrence SQLite/PostgreSQL)"
        ) from exc
    return admission


@transaction.atomic
def sortir_patient(admission_id, statut='SORTI', notes='', version=None):
    """Sortie hospitalière avec libération atomique du lit."""
    admission = lock_for_update(Admission.objects).select_related('lit').get(id=admission_id)
    if admission.lit_id:
        get_locked(Lit, pk=admission.lit_id)
    try:
        admission.sortir(statut=statut, notes=notes, version=version)
    except ValueError as exc:
        raise HospitalisationError(str(exc)) from exc
    return admission


@transaction.atomic
def transferer_patient(admission_id, nouveau_service_id, nouveau_lit_id, motif='', version=None):
    """Transfert inter-services avec changement de lit verrouillé."""
    admission = lock_for_update(Admission.objects).select_related('lit').get(id=admission_id)
    if admission.lit_id:
        get_locked(Lit, pk=admission.lit_id)
    nouveau_service = ServiceHospitalier.objects.get(id=nouveau_service_id, est_actif=True)
    nouveau_lit = get_locked(Lit, id=nouveau_lit_id)

    if nouveau_lit.chambre.service_id != nouveau_service_id:
        raise HospitalisationError("Le lit cible n'appartient pas au service de destination")

    try:
        admission.transferer(nouveau_service, nouveau_lit, motif=motif, version=version)
    except ValueError as exc:
        raise HospitalisationError(str(exc)) from exc
    return admission


def verifier_admission_pour_soins(admission_id):
    """Vérifie qu'une admission est active avant saisie de soins/constantes."""
    try:
        admission = Admission.objects.get(id=admission_id)
    except Admission.DoesNotExist:
        raise HospitalisationError("Admission introuvable")
    _verifier_admission_active(admission)
    return admission


def serialiser_admission(admission):
    return {
        "id": admission.id,
        "patient_id": admission.patient_id,
        "patient_nom": admission.patient.nom,
        "patient_prenom": admission.patient.prenom,
        "numero_dossier": admission.patient.numero_dossier,
        "service_id": admission.service_id,
        "service_nom": admission.service.nom,
        "lit_id": admission.lit_id,
        "lit_numero": admission.lit.numero if admission.lit else None,
        "lit_version": admission.lit.version if admission.lit else None,
        "medecin_referent_id": admission.medecin_referent_id,
        "medecin_referent": admission.medecin_referent.get_full_name() if admission.medecin_referent else None,
        "type_admission": admission.type_admission,
        "statut": admission.statut,
        "date_entree": admission.date_entree.isoformat(),
        "date_sortie": admission.date_sortie.isoformat() if admission.date_sortie else None,
        "date_previsionnelle_sortie": str(admission.date_previsionnelle_sortie) if admission.date_previsionnelle_sortie else None,
        "motif_hospitalisation": admission.motif_hospitalisation,
        "notes": admission.notes,
        "version": admission.version,
    }
