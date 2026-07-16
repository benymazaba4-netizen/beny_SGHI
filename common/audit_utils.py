from authentication.models import Utilisateur
from audit.models import AuditLog


def get_authenticated_user(request):
    payload = getattr(request, 'auth_payload', None)
    if not payload:
        return None
    try:
        return Utilisateur.objects.get(id=payload['id'])
    except Utilisateur.DoesNotExist:
        return None


def audit_log(request, action, instance, old_value='', new_value=''):
    """Enregistre une action dans le journal d'audit immuable."""
    user = get_authenticated_user(request)
    return AuditLog.log_action(
        utilisateur=user,
        action=action,
        instance=instance,
        old_value=old_value or '',
        new_value=new_value or '',
        request=request,
    )


def audit_login(request, user):
    return AuditLog.log_action(
        utilisateur=user,
        action='LOGIN',
        instance=user,
        new_value=f"Connexion réussie — rôle {user.role}",
        request=request,
    )
