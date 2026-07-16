from ninja import Router, Schema
from typing import List

from .models import Notification, DeviceToken
from .services import creer_notification
from common.permissions import auth_bearer, role_required, ROLE_ADMIN, ROLE_PATIENT, ROLE_MEDECIN
from common.audit_utils import get_authenticated_user

router = Router(auth=auth_bearer)


class DeviceTokenIn(Schema):
    token: str
    plateforme: str = 'ANDROID'


class NotificationOut(Schema):
    id: int
    type_notification: str
    titre: str
    corps: str
    lien: str
    est_lue: bool
    date_creation: str


@router.post("/devices", response={201: dict, 400: dict})
@role_required([ROLE_PATIENT, ROLE_MEDECIN, ROLE_ADMIN])
def register_device(request, payload: DeviceTokenIn):
    user = get_authenticated_user(request)
    if payload.plateforme not in ('ANDROID', 'IOS', 'WEB'):
        return 400, {"error": "Plateforme invalide"}
    device, _ = DeviceToken.objects.update_or_create(
        token=payload.token,
        defaults={
            'utilisateur': user,
            'plateforme': payload.plateforme,
            'est_actif': True,
        },
    )
    return 201, {"id": device.id, "message": "Appareil enregistré"}


@router.delete("/devices/{token_prefix}", response={200: dict, 404: dict})
@role_required([ROLE_PATIENT, ROLE_MEDECIN, ROLE_ADMIN])
def unregister_device(request, token_prefix: str):
    user = get_authenticated_user(request)
    deleted, _ = DeviceToken.objects.filter(
        utilisateur=user, token__startswith=token_prefix,
    ).delete()
    if not deleted:
        return 404, {"error": "Token introuvable"}
    return 200, {"message": "Appareil désenregistré"}


@router.get("/notifications", response={200: dict})
@role_required([ROLE_PATIENT, ROLE_MEDECIN, ROLE_ADMIN])
def list_notifications(request, non_lues: bool = False, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    user = get_authenticated_user(request)
    qs = Notification.objects.filter(utilisateur=user).order_by('-date_creation')
    if non_lues:
        qs = qs.filter(est_lue=False)
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    items = [
        {
            'id': n.id,
            'type_notification': n.type_notification,
            'titre': n.titre,
            'corps': n.corps,
            'lien': n.lien,
            'est_lue': n.est_lue,
            'date_creation': n.date_creation.isoformat(),
        }
        for n in rows
    ]
    return 200, paginated_response(items, meta)


@router.post("/notifications/{notif_id}/lue", response={200: dict, 404: dict})
@role_required([ROLE_PATIENT, ROLE_MEDECIN, ROLE_ADMIN])
def marquer_lue(request, notif_id: int):
    user = get_authenticated_user(request)
    try:
        notif = Notification.objects.get(id=notif_id, utilisateur=user)
    except Notification.DoesNotExist:
        return 404, {"error": "Notification introuvable"}
    notif.est_lue = True
    notif.save(update_fields=['est_lue'])
    return 200, {"message": "Notification marquée comme lue"}


@router.post("/notifications/test", response={201: NotificationOut})
@role_required([ROLE_ADMIN])
def test_notification(request):
    user = get_authenticated_user(request)
    notif = creer_notification(user, 'GENERAL', 'Test SGHI', 'Notification de test', push=False)
    return 201, {
        'id': notif.id,
        'type_notification': notif.type_notification,
        'titre': notif.titre,
        'corps': notif.corps,
        'lien': notif.lien,
        'est_lue': notif.est_lue,
        'date_creation': notif.date_creation.isoformat(),
    }
