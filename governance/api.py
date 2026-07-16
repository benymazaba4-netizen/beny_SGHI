from ninja import Router, Schema
from typing import List
from datetime import date

from .models import JournalAccesDossier, AnonymizationJob, ArchiveRecord
from .services import journaliser_acces, archiver_dossier_patient, lancer_anonymisation
from common.permissions import auth_bearer, role_required, ROLE_ADMIN
from common.audit_utils import audit_log, get_authenticated_user

router = Router(auth=auth_bearer)


class AnonymizationIn(Schema):
    nom: str
    periode_debut: date
    periode_fin: date


class AnonymizationOut(Schema):
    id: int
    nom: str
    statut: str
    nb_enregistrements: int
    date_creation: str


class AccesOut(Schema):
    id: int
    utilisateur: str
    patient_id: int
    action: str
    date_acces: str
    ip_address: str


@router.get("/acces-dossiers", response={200: dict})
@role_required([ROLE_ADMIN])
def list_acces_dossiers(request, patient_id: int = None, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = JournalAccesDossier.objects.select_related('utilisateur').order_by('-date_acces')
    if patient_id:
        qs = qs.filter(patient_id=patient_id)
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            'id': a.id,
            'utilisateur': a.utilisateur.username if a.utilisateur else '—',
            'patient_id': a.patient_id,
            'action': a.action,
            'date_acces': a.date_acces.isoformat(),
            'ip_address': str(a.ip_address or ''),
        }
        for a in rows
    ]
    return 200, paginated_response(items, meta)


@router.post("/patients/{patient_id}/archiver", response={200: dict, 404: dict})
@role_required([ROLE_ADMIN])
def archiver_patient(request, patient_id: int):
    user = get_authenticated_user(request)
    try:
        record = archiver_dossier_patient(patient_id, user)
    except Exception as exc:
        return 404, {"error": str(exc)}
    audit_log(request, 'ARCHIVE', record, new_value=f"Patient #{patient_id}")
    return 200, {"message": "Dossier archivé", "statut": record.statut}


@router.post("/anonymisation", response={201: AnonymizationOut})
@role_required([ROLE_ADMIN])
def create_anonymisation(request, payload: AnonymizationIn):
    user = get_authenticated_user(request)
    job = AnonymizationJob.objects.create(
        nom=payload.nom,
        periode_debut=payload.periode_debut,
        periode_fin=payload.periode_fin,
        lance_par=user,
    )
    lancer_anonymisation(job)
    audit_log(request, 'CREATE', job)
    return 201, {
        'id': job.id,
        'nom': job.nom,
        'statut': job.statut,
        'nb_enregistrements': job.nb_enregistrements,
        'date_creation': job.date_creation.isoformat(),
    }


@router.get("/anonymisation", response={200: dict})
@role_required([ROLE_ADMIN])
def list_anonymisation(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = AnonymizationJob.objects.order_by('-date_creation')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    items = [
        {
            'id': j.id,
            'nom': j.nom,
            'statut': j.statut,
            'nb_enregistrements': j.nb_enregistrements,
            'date_creation': j.date_creation.isoformat(),
        }
        for j in rows
    ]
    return 200, paginated_response(items, meta)


@router.get("/archives", response={200: dict})
@role_required([ROLE_ADMIN])
def list_archives(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = ArchiveRecord.objects.order_by('-date_archivage')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    items = [
        {
            'id': a.id,
            'object_id': a.object_id,
            'statut': a.statut,
            'date_archivage': a.date_archivage.isoformat() if a.date_archivage else None,
            'date_expiration_legale': a.date_expiration_legale.isoformat() if a.date_expiration_legale else None,
        }
        for a in rows
    ]
    return 200, paginated_response(items, meta)
