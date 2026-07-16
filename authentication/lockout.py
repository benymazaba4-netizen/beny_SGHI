"""Verrouillage temporaire de compte après échecs de connexion consécutifs."""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .connexion_log import journaliser_echec_connexion
from .models import Utilisateur


def max_attempts() -> int:
    return int(getattr(settings, 'ACCOUNT_LOCKOUT_MAX_ATTEMPTS', 5))


def lockout_minutes() -> int:
    return int(getattr(settings, 'ACCOUNT_LOCKOUT_MINUTES', 15))


def _get_user(username: str) -> Utilisateur | None:
    try:
        return Utilisateur.objects.get(username=username)
    except Utilisateur.DoesNotExist:
        return None


def _clear_expired_lockout(user: Utilisateur) -> bool:
    if not user.lockout_until:
        return False
    if timezone.now() >= user.lockout_until:
        user.failed_login_attempts = 0
        user.lockout_until = None
        user.save(update_fields=['failed_login_attempts', 'lockout_until'])
        return True
    return False


def is_account_locked(user: Utilisateur) -> bool:
    _clear_expired_lockout(user)
    return bool(user.lockout_until and timezone.now() < user.lockout_until)


def lockout_message(user: Utilisateur) -> str:
    remaining = user.lockout_until - timezone.now()
    total_seconds = max(0, int(remaining.total_seconds()))
    minutes = max(1, (total_seconds + 59) // 60)
    return f"Compte temporairement verrouillé. Réessayez dans {minutes} minute(s)."


def check_account_lockout(username: str) -> str | None:
    user = _get_user(username)
    if not user:
        return None
    if is_account_locked(user):
        return lockout_message(user)
    return None


def record_failed_login(request, username: str) -> None:
    user = _get_user(username)
    if not user:
        return
    user.failed_login_attempts += 1
    update_fields = ['failed_login_attempts']
    if user.failed_login_attempts >= max_attempts():
        user.lockout_until = timezone.now() + timedelta(minutes=lockout_minutes())
        update_fields.append('lockout_until')
    user.save(update_fields=update_fields)
    journaliser_echec_connexion(request, username)


def clear_failed_login_attempts(user: Utilisateur) -> None:
    if user.failed_login_attempts or user.lockout_until:
        user.failed_login_attempts = 0
        user.lockout_until = None
        user.save(update_fields=['failed_login_attempts', 'lockout_until'])
