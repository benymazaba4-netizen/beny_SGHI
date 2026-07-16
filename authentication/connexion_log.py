"""Journal des connexions SGHI."""

from .models import JournalConnexion


def journaliser_connexion(request, user, reussie=True):
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
    if not ip:
        ip = request.META.get('REMOTE_ADDR')
    JournalConnexion.objects.create(
        utilisateur=user,
        ip_address=ip or None,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        reussie=reussie,
    )
    if reussie and ip:
        user.ip_derniere_connexion = ip
        user.save(update_fields=['ip_derniere_connexion'])


def journaliser_echec_connexion(request, username: str):
    """Journalise une tentative de connexion échouée (identifiants ou MFA/OTP)."""
    from .models import Utilisateur
    try:
        user = Utilisateur.objects.get(username=username)
    except Utilisateur.DoesNotExist:
        return
    journaliser_connexion(request, user, reussie=False)
