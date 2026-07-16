from ninja import Router, Schema
from typing import List, Optional
from datetime import datetime, timedelta

from django.utils import timezone
from django.db.models import Q

from .models import RendezVous, DisponibiliteMedecin
from .services import creneaux_disponibles, confirmer_rendez_vous, serialiser_rdv
from common.permissions import (
    auth_bearer, role_required, enforce_patient_scope,
    ROLE_ADMIN, ROLE_MEDECIN, ROLE_SECRETAIRE, ROLE_PATIENT,
)
from common.audit_utils import audit_log, get_authenticated_user

router = Router(auth=auth_bearer)


class DisponibiliteIn(Schema):
    medecin_id: int
    service_id: int
    date_debut: datetime
    date_fin: datetime
    duree_creneau_minutes: int = 30


class RendezVousIn(Schema):
    patient_id: int
    medecin_id: int
    service_id: int
    date_heure: datetime
    motif: str
    duree_minutes: int = 30
    disponibilite_id: Optional[int] = None


class RendezVousOut(Schema):
    id: int
    patient_id: int
    patient: str
    medecin_id: int
    medecin: str
    service_id: int
    service: str
    date_heure: str
    duree_minutes: int
    motif: str
    statut: str
    notes: str


@router.post("/disponibilites", response={201: dict, 400: dict, 403: dict})
@role_required([ROLE_MEDECIN, ROLE_ADMIN, ROLE_SECRETAIRE])
def create_disponibilite(request, payload: DisponibiliteIn):
    if payload.date_fin <= payload.date_debut:
        return 400, {"error": "La date de fin doit être postérieure au début"}
    dispo = DisponibiliteMedecin.objects.create(**payload.dict())
    audit_log(request, 'CREATE', dispo)
    return 201, {"id": dispo.id, "message": "Disponibilité créée"}


@router.get("/disponibilites/creneaux", response={200: dict, 400: dict})
@role_required([ROLE_MEDECIN, ROLE_SECRETAIRE, ROLE_ADMIN, ROLE_PATIENT])
def list_creneaux(request, medecin_id: int, service_id: int, date_debut: str, date_fin: str,
                  page: int = 1, page_size: int = 50):
    from common.pagination import paginated_response
    try:
        debut = datetime.fromisoformat(date_debut.replace('Z', '+00:00'))
        fin = datetime.fromisoformat(date_fin.replace('Z', '+00:00'))
    except ValueError:
        return 400, {"error": "Format de date invalide (ISO 8601 attendu)"}
    creneaux = creneaux_disponibles(medecin_id, service_id, debut, fin)
    total = len(creneaux)
    page = max(1, int(page or 1))
    page_size = min(max(1, int(page_size or 20)), 100)
    offset = (page - 1) * page_size
    items = creneaux[offset:offset + page_size]
    total_pages = (total + page_size - 1) // page_size if total else 0
    meta = {
        'page': page,
        'page_size': page_size,
        'total': total,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_previous': page > 1,
    }
    return 200, paginated_response(items, meta)


@router.post("/rendez-vous", response={201: RendezVousOut, 400: dict, 403: dict})
@role_required([ROLE_PATIENT, ROLE_SECRETAIRE, ROLE_MEDECIN, ROLE_ADMIN])
def create_rendez_vous(request, payload: RendezVousIn):
    denied = enforce_patient_scope(request, payload.patient_id)
    if denied:
        return denied

    if payload.date_heure <= timezone.now():
        return 400, {"error": "La date doit être dans le futur"}

    conflit = RendezVous.objects.filter(
        medecin_id=payload.medecin_id,
        statut__in=['PLANIFIE', 'CONFIRME'],
        date_heure__lt=payload.date_heure + timedelta(minutes=payload.duree_minutes),
        date_heure__gte=payload.date_heure - timedelta(minutes=payload.duree_minutes),
    ).exists()
    if conflit:
        return 400, {"error": "Créneau déjà réservé pour ce médecin"}

    user = get_authenticated_user(request)
    rdv = RendezVous.objects.create(
        **payload.dict(),
        cree_par=user,
        statut='PLANIFIE',
    )
    confirmer_rendez_vous(rdv)
    audit_log(request, 'CREATE', rdv)
    try:
        from billing.secretariat_services import creer_invoice_consultation
        creer_invoice_consultation(
            patient_id=rdv.patient_id,
            rendez_vous_id=rdv.id,
        )
    except Exception:
        pass
    rdv = RendezVous.objects.select_related('patient', 'medecin', 'service').get(id=rdv.id)
    return 201, serialiser_rdv(rdv)


@router.get("/rendez-vous/patient/{patient_id}", response={200: dict, 403: dict})
@role_required([ROLE_PATIENT, ROLE_MEDECIN, ROLE_SECRETAIRE, ROLE_ADMIN])
def list_rdv_patient(request, patient_id: int, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    denied = enforce_patient_scope(request, patient_id)
    if denied:
        return denied
    qs = RendezVous.objects.filter(patient_id=patient_id).select_related(
        'patient', 'medecin', 'service',
    ).order_by('-date_heure')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    return 200, paginated_response([serialiser_rdv(r) for r in rows], meta)


@router.get("/rendez-vous/medecin/{medecin_id}", response={200: dict})
@role_required([ROLE_MEDECIN, ROLE_SECRETAIRE, ROLE_ADMIN])
def list_rdv_medecin(request, medecin_id: int, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = RendezVous.objects.filter(
        medecin_id=medecin_id,
        date_heure__gte=timezone.now() - timedelta(days=7),
    ).select_related('patient', 'medecin', 'service').order_by('date_heure')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    return 200, paginated_response([serialiser_rdv(r) for r in rows], meta)


@router.post("/rendez-vous/{rdv_id}/annuler", response={200: dict, 400: dict, 404: dict})
@role_required([ROLE_PATIENT, ROLE_SECRETAIRE, ROLE_MEDECIN, ROLE_ADMIN])
def annuler_rdv(request, rdv_id: int):
    try:
        rdv = RendezVous.objects.get(id=rdv_id)
    except RendezVous.DoesNotExist:
        return 404, {"error": "Rendez-vous introuvable"}

    denied = enforce_patient_scope(request, rdv.patient_id)
    if denied:
        return denied

    if not rdv.peut_etre_annule():
        return 400, {"error": "Ce rendez-vous ne peut plus être annulé"}
    rdv.statut = 'ANNULE'
    rdv.save(update_fields=['statut', 'date_modification'])
    audit_log(request, 'UPDATE', rdv, new_value='Annulé')
    return 200, {"message": "Rendez-vous annulé"}
