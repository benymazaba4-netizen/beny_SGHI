"""
Health check et monitoring endpoint
"""
from ninja import Router, Schema
from django.utils import timezone
from django.db import connection
from django.conf import settings
from typing import Optional
import psutil
import os

health_router = Router(tags=["monitoring"])


class HealthCheckResponse(Schema):
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    uptime_seconds: Optional[int] = None
    database_ok: bool
    cache_ok: bool
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    error: Optional[str] = None


START_TIME = timezone.now()


@health_router.get("/sante", response=HealthCheckResponse)
@health_router.get("/santé", response=HealthCheckResponse)
def health_check(request):
    """Endpoint de santé pour monitoring et orchestration."""
    checks = {
        "database": False,
        "cache": False,
    }
    errors = []
    
    # Check DB
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = True
    except Exception as e:
        errors.append(f"DB Error: {str(e)}")
    
    # Check Cache (Redis si configuré)
    try:
        from django.core.cache import cache
        cache.set("health_check", "ok", 10)
        if cache.get("health_check") == "ok":
            checks["cache"] = True
    except Exception as e:
        # Cache optionnel
        pass
    
    # Status global
    status = "healthy" if all(checks.values()) else ("degraded" if any(checks.values()) else "unhealthy")
    
    # Métriques système
    uptime = (timezone.now() - START_TIME).total_seconds()
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": status,
        "timestamp": timezone.now().isoformat(),
        "uptime_seconds": int(uptime),
        "database_ok": checks["database"],
        "cache_ok": checks["cache"],
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "error": " | ".join(errors) if errors else None,
    }


class KPIResponse(Schema):
    timestamp: str
    patients_actifs: int
    admissions_actives: int
    demandes_examens_en_attente: int
    factures_impayees: int
    stocks_en_alerte: int
    utilisateurs_connectes: Optional[int] = None


@health_router.get("/kpi", response=KPIResponse)
def get_kpis(request):
    """KPIs en temps réel pour dashboard administratif."""
    from clinical.models import Patient, Admission
    from laboratory.models import DemandeExamen
    from billing.models import Facture
    from pharmacy.models import AlerteStock
    
    kpis = {
        "timestamp": timezone.now().isoformat(),
        "patients_actifs": Patient.objects.filter(est_actif=True).count(),
        "admissions_actives": Admission.objects.filter(statut='EN_COURS').count(),
        "demandes_examens_en_attente": DemandeExamen.objects.filter(
            statut__in=['PRESCRIT', 'PRELEVE', 'EN_COURS', 'VALIDATION']
        ).count(),
        "factures_impayees": Facture.objects.filter(
            statut__in=['EMISE', 'IMPAYEE', 'PARTIELLE']
        ).count(),
        "stocks_en_alerte": AlerteStock.objects.filter(
            est_resolue=False
        ).count(),
    }
    
    return kpis


# Compteurs Prometheus (format texte)
_METRICS = {
    'sghi_requests_total': 0,
    'sghi_db_errors_total': 0,
}


@health_router.get("/metrics")
def prometheus_metrics(request):
    """Endpoint Prometheus — métriques applicatives."""
    from clinical.models import Patient, Admission
    from laboratory.models import DemandeExamen

    lines = [
        '# HELP sghi_patients_actifs Nombre de patients actifs',
        '# TYPE sghi_patients_actifs gauge',
        f'sghi_patients_actifs {Patient.objects.filter(est_actif=True).count()}',
        '# HELP sghi_admissions_actives Admissions en cours',
        '# TYPE sghi_admissions_actives gauge',
        f'sghi_admissions_actives {Admission.objects.filter(statut="EN_COURS").count()}',
        '# HELP sghi_examens_attente Examens en attente validation',
        '# TYPE sghi_examens_attente gauge',
        f'sghi_examens_attente {DemandeExamen.objects.filter(statut="VALIDATION").count()}',
        '# HELP sghi_uptime_seconds Uptime du serveur',
        '# TYPE sghi_uptime_seconds gauge',
        f'sghi_uptime_seconds {int((timezone.now() - START_TIME).total_seconds())}',
    ]
    from django.http import HttpResponse
    return HttpResponse('\n'.join(lines) + '\n', content_type='text/plain; charset=utf-8')

