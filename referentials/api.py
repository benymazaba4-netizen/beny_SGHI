from ninja import Router, Schema
from typing import List

from django.db.models import Q

from .models import CodeCIM10
from common.permissions import auth_bearer, role_required, ROLE_CLINICAL, ROLE_MEDECIN, ROLE_ADMIN

router = Router(auth=auth_bearer)


class CIM10Out(Schema):
    code: str
    libelle: str
    chapitre: str


@router.get("/cim10", response={200: dict})
@role_required(ROLE_CLINICAL + [ROLE_MEDECIN])
def search_cim10(request, q: str = '', page: int = 1, page_size: int = 20):
    from common.pagination import paginate_queryset, paginated_response
    qs = CodeCIM10.objects.filter(est_actif=True).order_by('code')
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(libelle__icontains=q))
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    items = [{'code': c.code, 'libelle': c.libelle, 'chapitre': c.chapitre} for c in rows]
    return 200, paginated_response(items, meta)


@router.get("/cim10/{code}", response={200: CIM10Out, 404: dict})
@role_required(ROLE_CLINICAL + [ROLE_MEDECIN])
def get_cim10(request, code: str):
    try:
        c = CodeCIM10.objects.get(code=code.upper(), est_actif=True)
    except CodeCIM10.DoesNotExist:
        return 404, {"error": "Code CIM-10 introuvable"}
    return 200, {'code': c.code, 'libelle': c.libelle, 'chapitre': c.chapitre}
