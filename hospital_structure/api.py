from ninja import Router, Schema
from typing import List, Optional
from .models import Batiment, ServiceHospitalier, Chambre, Lit
from common.permissions import (
    auth_bearer, role_required,
    ROLE_ADMIN, ROLE_MEDECIN, ROLE_SECRETAIRE, ROLE_INFIRMIER, ROLE_PATIENT,
)
from common.audit_utils import audit_log

router = Router(auth=auth_bearer)


class BatimentSchema(Schema):
    nom: str
    code: str
    adresse: str = ''
    nombre_etages: int = 1


class ServiceSchema(Schema):
    nom: str
    code: str
    batiment_id: int
    type_service: str = 'MEDICAL'
    telephone: str = ''
    email: str = ''
    etage: int = 0


class ChambreSchema(Schema):
    numero: str
    service_id: int
    type_chambre: str = 'DOUBLE'
    capacite_max: int = 2
    prix_par_jour: float = 0


class LitSchema(Schema):
    numero: str
    chambre_id: int
    statut: str = 'LIBRE'
    est_medicalise: bool = False


class BatimentOut(Schema):
    id: int
    nom: str
    code: str
    adresse: str = ''
    nombre_etages: int = 1


class ServiceOut(Schema):
    id: int
    nom: str
    code: str
    type_service: str = 'MEDICAL'


class ChambreOut(Schema):
    id: int
    numero: str
    service_id: int
    service_nom: str
    type_chambre: str
    capacite_max: int
    prix_par_jour: float


class LitOut(Schema):
    id: int
    numero: str
    statut: str
    chambre_id: int
    service_nom: str


@router.post("/batiments", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def create_batiment(request, payload: BatimentSchema):
    try:
        batiment = Batiment.objects.create(**payload.dict())
        audit_log(request, 'CREATE', batiment, new_value=str(payload.dict()))
        return 201, {"id": batiment.id, "message": "Bâtiment créé"}
    except Exception as e:
        return 400, {"error": str(e)}


@router.get("/batiments", response={200: dict, 401: dict})
@role_required([ROLE_ADMIN, ROLE_MEDECIN, ROLE_SECRETAIRE, ROLE_INFIRMIER])
def list_batiments(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Batiment.objects.all().order_by('code')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    items = [
        {"id": b.id, "nom": b.nom, "code": b.code, "adresse": b.adresse, "nombre_etages": b.nombre_etages}
        for b in rows
    ]
    return 200, paginated_response(items, meta)


@router.post("/services", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def create_service(request, payload: ServiceSchema):
    try:
        service = ServiceHospitalier.objects.create(**payload.dict())
        audit_log(request, 'CREATE', service, new_value=str(payload.dict()))
        return 201, {"id": service.id, "message": "Service créé"}
    except Exception as e:
        return 400, {"error": str(e)}


@router.get("/services", response={200: dict, 401: dict})
@role_required([ROLE_ADMIN, ROLE_MEDECIN, ROLE_SECRETAIRE, ROLE_INFIRMIER, ROLE_PATIENT])
def list_services(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = ServiceHospitalier.objects.filter(est_actif=True).order_by('code')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    items = [{"id": s.id, "nom": s.nom, "code": s.code, "type_service": s.type_service} for s in rows]
    return 200, paginated_response(items, meta)


@router.post("/chambres", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def create_chambre(request, payload: ChambreSchema):
    try:
        chambre = Chambre.objects.create(**payload.dict())
        audit_log(request, 'CREATE', chambre, new_value=str(payload.dict()))
        return 201, {"id": chambre.id, "message": "Chambre créée"}
    except Exception as e:
        return 400, {"error": str(e)}


@router.get("/chambres", response={200: dict, 401: dict})
@role_required([ROLE_ADMIN, ROLE_MEDECIN, ROLE_SECRETAIRE])
def list_chambres(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Chambre.objects.filter(est_actif=True).select_related('service').order_by('service__code', 'numero')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    items = [
        {
            "id": c.id, "numero": c.numero, "service_id": c.service_id,
            "service_nom": c.service.nom, "type_chambre": c.type_chambre,
            "capacite_max": c.capacite_max, "prix_par_jour": float(c.prix_par_jour),
        }
        for c in rows
    ]
    return 200, paginated_response(items, meta)


@router.post("/lits", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def create_lit(request, payload: LitSchema):
    try:
        lit = Lit.objects.create(**payload.dict())
        audit_log(request, 'CREATE', lit, new_value=str(payload.dict()))
        return 201, {"id": lit.id, "message": "Lit créé"}
    except Exception as e:
        return 400, {"error": str(e)}


@router.get("/lits", response={200: dict, 401: dict})
@role_required([ROLE_ADMIN, ROLE_MEDECIN, ROLE_SECRETAIRE])
def list_lits(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Lit.objects.select_related('chambre__service').order_by('chambre__service__code', 'numero')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            "id": l.id, "numero": l.numero, "statut": l.statut, "version": l.version,
            "chambre_id": l.chambre_id, "service_nom": l.chambre.service.nom,
        }
        for l in rows
    ]
    return 200, paginated_response(items, meta)


@router.get("/lits/libres", response={200: dict, 401: dict})
@role_required([ROLE_ADMIN, ROLE_MEDECIN, ROLE_SECRETAIRE])
def get_lits_libres(request, service_id: Optional[int] = None, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Lit.objects.filter(
        statut='LIBRE',
        patient_actuel__isnull=True,
        chambre__est_actif=True,
    ).exclude(statut='HORS_SERVICE').select_related('chambre__service').order_by('numero')
    if service_id:
        qs = qs.filter(chambre__service_id=service_id)
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            "id": l.id,
            "numero": l.numero,
            "version": l.version,
            "chambre_id": l.chambre_id,
            "chambre_numero": l.chambre.numero,
            "service_nom": l.chambre.service.nom,
        }
        for l in rows
    ]
    return 200, paginated_response(items, meta)
