import secrets
import hashlib
import datetime
from django.utils import timezone
from django.conf import settings

from .models import RefreshToken


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def create_refresh_token(user, request=None, days: int = None):
    """Crée et enregistre un refresh token (retourne le token brut et l'objet DB).

    Le token stocké en DB est hashé pour éviter fuite éventuelle.
    """
    raw = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw)
    expires_days = days or getattr(settings, 'REFRESH_TOKEN_DAYS', 30)
    expires_at = timezone.now() + datetime.timedelta(days=expires_days)

    ip = None
    ua = ''
    if request is not None:
        ip = request.META.get('REMOTE_ADDR')
        ua = request.META.get('HTTP_USER_AGENT', '')

    rt = RefreshToken.objects.create(
        user=user,
        token_hash=token_hash,
        expires_at=expires_at,
        ip_address=ip,
        user_agent=ua,
    )
    return raw, rt


def get_refresh_token_obj(raw_token: str):
    token_hash = _hash_token(raw_token)
    try:
        return RefreshToken.objects.get(token_hash=token_hash)
    except RefreshToken.DoesNotExist:
        return None


def rotate_refresh_token(raw_token: str, request=None):
    """Rotates the given refresh token and returns (new_raw, new_obj, user).

    Raises ValueError on invalid/expired/revoked tokens.
    """
    rt = get_refresh_token_obj(raw_token)
    if not rt:
        raise ValueError("Refresh token invalide")
    if rt.revoked:
        raise ValueError("Refresh token révoqué")
    if rt.is_expired():
        raise ValueError("Refresh token expiré")

    # create replacement
    new_raw, new_rt = create_refresh_token(rt.user, request=request)

    # mark old revoked and link
    rt.revoked = True
    rt.replaced_by = new_rt
    rt.save()

    return new_raw, new_rt, rt.user


def revoke_refresh_token(raw_token: str):
    rt = get_refresh_token_obj(raw_token)
    if not rt:
        return False
    rt.revoke()
    return True
