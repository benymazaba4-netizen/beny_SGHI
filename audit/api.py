from ninja import Router, Schema
from typing import List, Optional
from .models import AuditLog
from common.permissions import auth_bearer, role_required, ROLE_ADMIN

router = Router(auth=auth_bearer)


class AuditLogSchema(Schema):
    id_log: int
    timestamp: str
    utilisateur_username: str
    utilisateur_ip: Optional[str] = None
    action: str
    app_name: str
    model_name: str
    object_id: str
    old_value: str
    new_value: str
    request_path: str = ''


def _serialiser_log(log):
    return {
        "id_log": log.id_log,
        "timestamp": log.timestamp.isoformat(),
        "utilisateur_username": log.utilisateur_username,
        "utilisateur_ip": log.utilisateur_ip,
        "action": log.action,
        "app_name": log.app_name,
        "model_name": log.model_name,
        "object_id": log.object_id,
        "old_value": log.old_value,
        "new_value": log.new_value,
        "request_path": log.request_path,
    }


@router.get("/logs", response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def get_audit_logs(request, app_name: Optional[str] = None, action: Optional[str] = None, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = AuditLog.objects.all().order_by('-timestamp')
    if app_name:
        qs = qs.filter(app_name=app_name)
    if action:
        qs = qs.filter(action=action)
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    return 200, paginated_response([_serialiser_log(log) for log in rows], meta)


@router.get("/logs/{log_id}", response={200: AuditLogSchema, 401: dict, 403: dict, 404: dict})
@role_required([ROLE_ADMIN])
def get_audit_log(request, log_id: int):
    try:
        log = AuditLog.objects.get(id_log=log_id)
        return 200, _serialiser_log(log)
    except AuditLog.DoesNotExist:
        return 404, {"error": "Log non trouvé"}
