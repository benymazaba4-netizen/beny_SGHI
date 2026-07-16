from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from ninja import Router

from billing.models import Facture
from clinical.models import Admission
from common.permissions import ROLE_ADMIN, auth_bearer, role_required
from hospital_structure.models import Lit
from laboratory.models import DemandeExamen

router = Router(auth=auth_bearer)

ADMIN_STATS_CACHE_KEY = 'sghi_admin_stats_v1'
ADMIN_STATS_CACHE_TTL = 120


def _percent(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((value / total) * 100, 2)


def _serie_map(queryset, date_field: str, value_field: str | None = None) -> dict:
    rows = queryset.annotate(day=TruncDate(date_field)).values('day')
    if value_field:
        rows = rows.annotate(value=Sum(value_field))
    else:
        rows = rows.annotate(value=Count('id'))
    return {row['day'].isoformat(): float(row['value'] or 0) for row in rows if row['day']}


def _last_days_series(days: int = 7):
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    labels = [(start + timedelta(days=i)).isoformat() for i in range(days)]

    revenue = _serie_map(
        Facture.objects.filter(
            statut__in=['PAYEE', 'PARTIELLE'],
            date_emission__date__gte=start,
        ),
        'date_emission',
        'montant_paye',
    )
    admissions = _serie_map(
        Admission.objects.filter(date_entree__date__gte=start),
        'date_entree',
    )
    lab = _serie_map(
        DemandeExamen.objects.filter(date_prescription__date__gte=start),
        'date_prescription',
    )

    return {
        'labels': labels,
        'recettes': [revenue.get(day, 0.0) for day in labels],
        'admissions': [admissions.get(day, 0.0) for day in labels],
        'examens': [lab.get(day, 0.0) for day in labels],
    }


def _compute_admin_stats():
    total_lits = Lit.objects.count()
    lits_occupes = Lit.objects.filter(statut='OCCUPE').count()
    admissions_actives = Admission.objects.filter(statut='EN_COURS').count()

    recettes = Facture.objects.filter(
        statut__in=['PAYEE', 'PARTIELLE'],
    ).aggregate(total=Sum('montant_paye'))['total'] or 0

    lis_counts = {
        row['statut']: row['total']
        for row in DemandeExamen.objects.values('statut').annotate(total=Count('id'))
    }
    examens_attente = sum(lis_counts.get(statut, 0) for statut in ('PRESCRIT', 'PRELEVE', 'EN_COURS', 'VALIDATION'))
    examens_publies = DemandeExamen.objects.filter(resultat__est_publie=True).count()

    return {
        'occupation': {
            'total_lits': total_lits,
            'lits_occupes': lits_occupes,
            'taux': _percent(lits_occupes, total_lits),
        },
        'finances': {
            'recettes_globales': float(recettes),
            'factures_validees': Facture.objects.filter(statut__in=['PAYEE', 'PARTIELLE']).count(),
        },
        'laboratoire': {
            'attente': examens_attente,
            'publies': examens_publies,
            'par_statut': lis_counts,
        },
        'admissions': {
            'actives': admissions_actives,
        },
        'trends': _last_days_series(),
        'cache': {
            'ttl_seconds': ADMIN_STATS_CACHE_TTL,
            'generated_at': timezone.now().isoformat(),
            'hit': False,
        },
    }


@router.get("/stats", response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def admin_stats(request):
    cached = cache.get(ADMIN_STATS_CACHE_KEY)
    if cached:
        cached['cache'] = {**cached.get('cache', {}), 'hit': True}
        return 200, cached

    payload = _compute_admin_stats()
    cache.set(ADMIN_STATS_CACHE_KEY, payload, ADMIN_STATS_CACHE_TTL)
    return 200, payload
