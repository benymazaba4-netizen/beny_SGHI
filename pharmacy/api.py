from ninja import Router, Schema
from typing import List, Optional
from datetime import date
from .models import Lot, Stock, MouvementStock, AlerteStock
from .services import creer_lot
from prescriptions.models import Medicament
from common.permissions import (
    auth_bearer, role_required,
    ROLE_ADMIN, ROLE_PHARMACIEN, ROLE_MEDECIN,
)
from common.audit_utils import audit_log

router = Router(auth=auth_bearer)

class LotSchema(Schema):
    medicament_id: int
    numero_lot: str
    quantite_initiale: int
    date_fabrication: date
    date_peremption: date
    fournisseur: str = ''
    prix_achat: float = 0

class MouvementSchema(Schema):
    medicament_id: int
    type_mouvement: str
    quantite: int
    reference: str = ''
    commentaire: str = ''

@router.post("/lots", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_PHARMACIEN])
def create_lot(request, payload: LotSchema):
    try:
        lot = creer_lot(payload.dict())
        audit_log(request, 'CREATE', lot, new_value=str(payload.dict()))
        return 201, {"id": lot.id, "message": "Lot ajouté"}
    except Exception as e:
        return 400, {"error": str(e)}

@router.get("/stocks", response={200: dict, 401: dict})
@role_required([ROLE_ADMIN, ROLE_PHARMACIEN, ROLE_MEDECIN])
def get_stocks(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Stock.objects.select_related('medicament').order_by('medicament__nom')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            'id': s.id,
            'medicament__code': s.medicament.code,
            'medicament__nom': s.medicament.nom,
            'quantite_totale': s.quantite_totale,
            'seuil_alerte': s.seuil_alerte,
        }
        for s in rows
    ]
    return 200, paginated_response(items, meta)

@router.get("/alertes", response={200: dict, 401: dict})
@role_required([ROLE_ADMIN, ROLE_PHARMACIEN])
def get_alertes(request, non_lues: bool = False, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = AlerteStock.objects.filter(est_resolue=False).select_related('medicament').order_by('-date_creation')
    if non_lues:
        qs = qs.filter(est_lue=False)
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            'id': a.id,
            'medicament__nom': a.medicament.nom,
            'type_alerte': a.type_alerte,
            'message': a.message,
            'date_creation': a.date_creation.isoformat(),
        }
        for a in rows
    ]
    return 200, paginated_response(items, meta)

@router.post("/mouvements", response={201: dict, 400: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_PHARMACIEN])
def create_mouvement(request, payload: MouvementSchema):
    try:
        mouvement = MouvementStock.objects.create(**payload.dict())
        stock = Stock.objects.get(medicament_id=payload.medicament_id)
        stock.mettre_a_jour()

        if stock.est_alerte():
            AlerteStock.objects.create(
                medicament_id=payload.medicament_id,
                type_alerte='SEUIL',
                message=f"Stock faible: {stock.quantite_totale} unités restantes"
            )
        audit_log(request, 'CREATE', mouvement, new_value=str(payload.dict()))
        return 201, {"id": mouvement.id, "message": "Mouvement enregistré"}
    except Exception as e:
        return 400, {"error": str(e)}
