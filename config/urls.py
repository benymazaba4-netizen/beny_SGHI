from django.urls import path
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from ninja import NinjaAPI

from authentication.api import router as auth_router
from authentication.mfa_api import mfa_router
from clinical.api import router as clinical_router
from hospital_structure.api import router as hospital_router
from prescriptions.api import router as prescription_router
from pharmacy.api import router as pharmacy_router
from laboratory.api import router as laboratory_router
from billing.api import router as billing_router
from rh.api import router as rh_router
from audit.api import router as audit_router
from dashboard.api import router as dashboard_router
from appointments.api import router as appointments_router
from messaging.api import router as messaging_router
from notifications.api import router as notifications_router
from referentials.api import router as referentials_router
from governance.api import router as governance_router
from interop.api import router as interop_router
from admin_stats.api import router as admin_stats_router
from secretariat.api import router as secretariat_router
from common.monitoring import health_router
from common.upload_api import router as upload_router

api = NinjaAPI(
    title="SGHI - Système de Gestion Hospitalière",
    version="1.0.0",
    description="API REST pour l'ERP Médical Intégré (v1)",
)

api.add_router("/auth/", auth_router)
api.add_router("/mfa/", mfa_router)
api.add_router("/clinical/", clinical_router)
api.add_router("/hospital/", hospital_router)
api.add_router("/prescriptions/", prescription_router)
api.add_router("/pharmacy/", pharmacy_router)
api.add_router("/laboratory/", laboratory_router)
api.add_router("/billing/", billing_router)
api.add_router("/rh/", rh_router)
api.add_router("/audit/", audit_router)
api.add_router("/dashboard/", dashboard_router)
api.add_router("/appointments/", appointments_router)
api.add_router("/messaging/", messaging_router)
api.add_router("/notifications/", notifications_router)
api.add_router("/referentials/", referentials_router)
api.add_router("/governance/", governance_router)
api.add_router("/fhir/", interop_router)
api.add_router("/admin/", admin_stats_router)
api.add_router("/secretariat/", secretariat_router)
api.add_router("/files/", upload_router)
api.add_router("", health_router)

urlpatterns = [
    path('', RedirectView.as_view(url='/api/v1/docs', permanent=False)),
    path('api/v1/', api.urls),
    path('api/', RedirectView.as_view(url='/api/v1/docs', permanent=False)),
]

if getattr(settings, 'DJANGO_ADMIN_ENABLED', False):
    from django.contrib import admin
    urlpatterns.insert(1, path('admin/', admin.site.urls))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
