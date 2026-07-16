from ninja import Router, Schema
from typing import List, Optional

from .models import Conversation, Message
from common.permissions import (
    auth_bearer, role_required, enforce_patient_scope, get_patient_id_for_user,
    ROLE_ADMIN, ROLE_MEDECIN, ROLE_PATIENT,
)
from common.audit_utils import audit_log, get_authenticated_user
from governance.services import journaliser_acces

router = Router(auth=auth_bearer)


class MessageIn(Schema):
    contenu: str


class ConversationIn(Schema):
    patient_id: int
    medecin_id: int
    sujet: str = ''


class MessageOut(Schema):
    id: int
    expediteur: str
    expediteur_id: int
    contenu: str
    est_lu: bool
    date_envoi: str


class ConversationOut(Schema):
    id: int
    patient_id: int
    patient: str
    medecin_id: int
    medecin: str
    sujet: str
    nb_non_lus: int
    date_dernier_message: str


def _serialiser_conversation(conv, user):
    nb_non_lus = conv.messages.filter(est_lu=False).exclude(expediteur=user).count()
    return {
        'id': conv.id,
        'patient_id': conv.patient_id,
        'patient': f"{conv.patient.nom} {conv.patient.prenom}",
        'medecin_id': conv.medecin_id,
        'medecin': conv.medecin.get_full_name() or conv.medecin.username,
        'sujet': conv.sujet,
        'nb_non_lus': nb_non_lus,
        'date_dernier_message': conv.date_dernier_message.isoformat(),
    }


@router.get("/conversations", response={200: dict})
@role_required([ROLE_MEDECIN, ROLE_PATIENT, ROLE_ADMIN])
def list_conversations(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    user = get_authenticated_user(request)
    if user.role == ROLE_PATIENT:
        patient_id = get_patient_id_for_user(user)
        qs = Conversation.objects.filter(patient_id=patient_id, est_active=True)
    elif user.role == ROLE_MEDECIN:
        qs = Conversation.objects.filter(medecin=user, est_active=True)
    else:
        qs = Conversation.objects.filter(est_active=True)

    qs = qs.select_related('patient', 'medecin').order_by('-date_dernier_message')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    return 200, paginated_response([_serialiser_conversation(c, user) for c in rows], meta)


@router.post("/conversations", response={201: ConversationOut, 400: dict})
@role_required([ROLE_MEDECIN, ROLE_PATIENT, ROLE_ADMIN])
def create_conversation(request, payload: ConversationIn):
    denied = enforce_patient_scope(request, payload.patient_id)
    if denied:
        return denied

    conv, created = Conversation.objects.get_or_create(
        patient_id=payload.patient_id,
        medecin_id=payload.medecin_id,
        defaults={'sujet': payload.sujet},
    )
    if not created and payload.sujet:
        conv.sujet = payload.sujet
        conv.save(update_fields=['sujet'])

    user = get_authenticated_user(request)
    journaliser_acces(request, payload.patient_id, 'CONVERSATION')
    return 201, _serialiser_conversation(
        Conversation.objects.select_related('patient', 'medecin').get(id=conv.id),
        user,
    )


@router.get("/conversations/{conv_id}/messages", response={200: dict, 403: dict, 404: dict})
@role_required([ROLE_MEDECIN, ROLE_PATIENT, ROLE_ADMIN])
def list_messages(request, conv_id: int, since_id: Optional[int] = None, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    try:
        conv = Conversation.objects.select_related('patient').get(id=conv_id)
    except Conversation.DoesNotExist:
        return 404, {"error": "Conversation introuvable"}

    denied = enforce_patient_scope(request, conv.patient_id)
    if denied:
        return denied

    journaliser_acces(request, conv.patient_id, 'LECTURE_MESSAGES')
    qs = conv.messages.select_related('expediteur').order_by('date_envoi')
    if since_id:
        qs = qs.filter(id__gt=since_id)

    user = get_authenticated_user(request)
    conv.messages.filter(est_lu=False).exclude(expediteur=user).update(est_lu=True)

    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            'id': m.id,
            'expediteur': m.expediteur.get_full_name() or m.expediteur.username,
            'expediteur_id': m.expediteur_id,
            'contenu': m.contenu,
            'est_lu': m.est_lu,
            'date_envoi': m.date_envoi.isoformat(),
        }
        for m in rows
    ]
    return 200, paginated_response(items, meta)


@router.post("/conversations/{conv_id}/messages", response={201: MessageOut, 400: dict, 404: dict})
@role_required([ROLE_MEDECIN, ROLE_PATIENT, ROLE_ADMIN])
def send_message(request, conv_id: int, payload: MessageIn):
    if not payload.contenu.strip():
        return 400, {"error": "Message vide"}

    try:
        conv = Conversation.objects.get(id=conv_id, est_active=True)
    except Conversation.DoesNotExist:
        return 404, {"error": "Conversation introuvable"}

    denied = enforce_patient_scope(request, conv.patient_id)
    if denied:
        return denied

    user = get_authenticated_user(request)
    msg = Message.objects.create(
        conversation=conv,
        expediteur=user,
        contenu=payload.contenu.strip(),
    )
    conv.save(update_fields=['date_dernier_message'])
    audit_log(request, 'CREATE', msg)

    from notifications.services import creer_notification
    if user.role == ROLE_PATIENT:
        destinataire = conv.medecin
    else:
        destinataire = conv.patient.utilisateur
    if destinataire and destinataire.id != user.id:
        creer_notification(
            destinataire,
            'MESSAGE',
            'Nouveau message',
            payload.contenu[:100],
            push=True,
        )

    return 201, {
        'id': msg.id,
        'expediteur': user.get_full_name() or user.username,
        'expediteur_id': user.id,
        'contenu': msg.contenu,
        'est_lu': msg.est_lu,
        'date_envoi': msg.date_envoi.isoformat(),
    }
