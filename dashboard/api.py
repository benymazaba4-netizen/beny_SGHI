from ninja import Router, Schema
from typing import Dict, Any
from django.db.models import Count, Sum
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from clinical.models import Admission, Consultation
from billing.models import Facture, TransactionPaiement
from laboratory.models import DemandeExamen
from hospital_structure.models import Lit
from dashboard.models import KPICache
from common.permissions import auth_bearer, role_required, ROLE_ADMIN, ROLE_COMPTABLE, ROLE_MEDECIN

router = Router(auth=auth_bearer)

CACHE_KEY = 'sghi_dashboard_kpis'
CACHE_TTL = 60


class KPISchema(Schema):
    taux_occupation: float
    recettes_jour: float
    recettes_mois: float
    patients_admis_jour: int
    examens_attente: int
    prescriptions_jour: int
    cache_hit: bool = False


def _compute_kpis():
    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    total_lits = Lit.objects.count() or 1
    lits_occupes = Admission.objects.filter(statut='EN_COURS').count()
    taux_occupation = (lits_occupes / total_lits * 100) if total_lits > 0 else 0

    recettes_jour = TransactionPaiement.objects.filter(
        date_transaction__date=today,
        statut='SUCCESS'
    ).aggregate(total=Sum('montant'))['total'] or 0

    recettes_mois = TransactionPaiement.objects.filter(
        date_transaction__date__gte=start_of_month,
        statut='SUCCESS'
    ).aggregate(total=Sum('montant'))['total'] or 0

    return {
        "taux_occupation": round(taux_occupation, 2),
        "recettes_jour": float(recettes_jour),
        "recettes_mois": float(recettes_mois),
        "patients_admis_jour": Admission.objects.filter(date_entree__date=today).count(),
        "examens_attente": DemandeExamen.objects.filter(statut='VALIDATION').count(),
        "prescriptions_jour": Consultation.objects.filter(date_consultation__date=today).count(),
    }


@router.get("/kpis", response={200: KPISchema, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_COMPTABLE, ROLE_MEDECIN])
def get_kpis(request):
    cached = cache.get(CACHE_KEY)
    if cached:
        return 200, {**cached, "cache_hit": True}

    kpis = _compute_kpis()
    cache.set(CACHE_KEY, kpis, CACHE_TTL)

    import json
    KPICache.objects.update_or_create(
        type_kpi='OCCUPATION',
        defaults={
            'valeur': json.dumps(kpis),
            'date_expiration': timezone.now() + timedelta(seconds=CACHE_TTL),
        },
    )

    return 200, {**kpis, "cache_hit": False}
