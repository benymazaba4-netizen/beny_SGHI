"""OTP par e-mail — double authentification dynamique pour tous les utilisateurs."""
import logging
import random
import uuid

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import EmailValidator

logger = logging.getLogger(__name__)

OTP_EMAIL_ERROR = (
    "Cet utilisateur ne possède pas d'adresse e-mail valide pour la double authentification."
)

_email_validator = EmailValidator()


def resolve_user_email(user) -> str | None:
    """Retourne l'e-mail du compte utilisateur (tout domaine valide : Gmail, Yahoo, Outlook, pro…)."""
    email = (getattr(user, 'email', None) or '').strip()
    if not email:
        return None
    try:
        _email_validator(email)
    except ValidationError:
        return None
    return email


def mask_email(email: str) -> str:
    if not email or '@' not in email:
        return ''
    local, domain = email.split('@', 1)
    masked_local = f"{local[0]}***" if local else '***'
    return f"{masked_local}@{domain}"


def create_login_otp(user, *, request=None) -> tuple[str | None, str | None, str | None]:
    """
    Génère un OTP et l'envoie à user.email.
    Retourne (session_id, email_hint, error).
    """
    if not resolve_user_email(user):
        return None, None, OTP_EMAIL_ERROR

    code = f"{random.randint(0, 999999):06d}"
    session_id = str(uuid.uuid4())
    ttl = int(getattr(settings, 'OTP_EXPIRY_SECONDS', 600))

    cache.set(
        f"otp_login_{session_id}",
        {
            'user_id': user.id,
            'username': user.username,
            'email': user.email.strip(),
            'code': code,
            'attempts': 0,
            'resend_count': 0,
        },
        ttl,
    )

    old_session = cache.get(f"otp_user_{user.id}")
    if old_session:
        cache.delete(f"otp_login_{old_session}")
    cache.set(f"otp_user_{user.id}", session_id, ttl)

    err = _send_otp_email(user, code, session_id, ttl)
    if err:
        return None, None, err

    return session_id, mask_email(user.email), None


def resend_login_otp(session_id: str, *, request=None) -> tuple[str | None, str | None, str | None]:
    """Renvoie un nouveau code OTP à user.email (max 3 renvois)."""
    key = f"otp_login_{session_id}"
    data = cache.get(key)
    if not data:
        return None, None, "Session OTP expirée — reconnectez-vous."

    resend_count = data.get('resend_count', 0)
    max_resends = int(getattr(settings, 'OTP_MAX_RESENDS', 3))
    if resend_count >= max_resends:
        cache.delete(key)
        return None, None, "Trop de renvois — reconnectez-vous."

    from authentication.models import Utilisateur
    try:
        user = Utilisateur.objects.get(id=data['user_id'], is_active=True)
    except Utilisateur.DoesNotExist:
        cache.delete(key)
        return None, None, "Utilisateur invalide."

    if not resolve_user_email(user):
        return None, None, OTP_EMAIL_ERROR

    code = f"{random.randint(0, 999999):06d}"
    ttl = int(getattr(settings, 'OTP_EXPIRY_SECONDS', 600))
    data['code'] = code
    data['email'] = user.email.strip()
    data['attempts'] = 0
    data['resend_count'] = resend_count + 1
    cache.set(key, data, ttl)

    err = _send_otp_email(user, code, session_id, ttl, is_resend=True)
    if err:
        return None, None, err

    logger.info("OTP renvoye a %s pour le compte %s (renvoi %s)", user.email, user.username, data['resend_count'])
    return session_id, mask_email(user.email), None


def _send_otp_email(user, code: str, session_id: str, ttl: int, *, is_resend=False) -> str | None:
    """Envoie l'OTP via send_mail à user.email. Retourne un message d'erreur ou None."""
    recipient = resolve_user_email(user)
    if not recipient:
        return OTP_EMAIL_ERROR

    subject = "SGHI ERP - Votre code de validation"
    if is_resend:
        subject = "SGHI ERP - Nouveau code de validation"

    message = f"Votre code OTP est : {code}"
    from_email = settings.EMAIL_HOST_USER or settings.DEFAULT_FROM_EMAIL

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient],
            fail_silently=False,
        )
        logger.info("OTP envoye a %s pour le compte %s", recipient, user.username)
        return None
    except Exception as exc:
        logger.error("Echec envoi OTP a %s : %s", recipient, exc)

        use_local_smtp = (
            settings.EMAIL_HOST in ('127.0.0.1', 'localhost', 'mailpit')
            or not getattr(settings, 'EMAIL_USE_REAL_SMTP', False)
        )
        if getattr(settings, 'DEBUG', False) and use_local_smtp:
            logger.warning(
                "OTP dev (SMTP local) — compte %s, code %s, destinataire %s",
                user.username,
                code,
                recipient,
            )
            return None

        cache.delete(f"otp_login_{session_id}")
        cache.delete(f"otp_user_{user.id}")
        return (
            "Impossible d'envoyer le code OTP par e-mail. "
            "Vérifiez la configuration SMTP dans .env"
        )


def verify_login_otp(session_id: str, code: str) -> tuple[int | None, str | None]:
    """Vérifie l'OTP. Retourne (user_id, error)."""
    key = f"otp_login_{session_id}"
    data = cache.get(key)
    if not data:
        return None, "Session OTP expirée — reconnectez-vous."

    attempts = data.get('attempts', 0)
    if attempts >= 5:
        cache.delete(key)
        user_id = data.get('user_id')
        if user_id:
            cache.delete(f"otp_user_{user_id}")
        return None, "Trop de tentatives — reconnectez-vous."

    submitted = (code or '').strip().replace(' ', '')
    dev_code = getattr(settings, 'OTP_DEV_BYPASS_CODE', '123456')
    if getattr(settings, 'DEBUG', False) and submitted == dev_code:
        user_id = data.get('user_id')
        cache.delete(key)
        if user_id:
            cache.delete(f"otp_user_{user_id}")
        logger.warning("OTP dev bypass accepte pour user_id=%s", user_id)
        return user_id, None

    if submitted != data.get('code'):
        data['attempts'] = attempts + 1
        ttl = int(getattr(settings, 'OTP_EXPIRY_SECONDS', 600))
        cache.set(key, data, ttl)
        return None, "Code OTP invalide ou expiré."

    user_id = data.get('user_id')
    cache.delete(key)
    if user_id:
        cache.delete(f"otp_user_{user_id}")
    return user_id, None


def _resolve_user_by_identifier(identifier: str):
    from authentication.models import Utilisateur

    ident = (identifier or '').strip()
    if not ident:
        return None
    if '@' in ident:
        return Utilisateur.objects.filter(email__iexact=ident, is_active=True).first()
    return Utilisateur.objects.filter(username=ident, is_active=True).first()


def verify_login_otp_by_identifier(identifier: str, code: str) -> tuple[int | None, str | None]:
    """Vérifie l'OTP via nom d'utilisateur ou e-mail (2FA)."""
    user = _resolve_user_by_identifier(identifier)
    if not user:
        return None, "Identifiant invalide."

    session_id = cache.get(f"otp_user_{user.id}")
    if not session_id:
        return None, "Code expiré ou aucune demande en cours — reconnectez-vous."

    return verify_login_otp(session_id, code)
