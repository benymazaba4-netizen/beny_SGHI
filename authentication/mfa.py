"""
MFA (Multi-Factor Authentication) — TOTP (Time-based One-Time Password)
"""
import pyotp
import qrcode
import io
import base64
from django.conf import settings


def generate_totp_secret(user_id: int) -> str:
    """Génère un secret TOTP unique pour l'utilisateur."""
    return pyotp.random_base32()


def get_totp_uri(user_username: str, secret: str) -> str:
    """Génère l'URI TOTP (pour QR code)."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=user_username,
        issuer_name="SGHI ERP Médical"
    )


def generate_qr_code_base64(totp_uri: str) -> str:
    """Génère un QR code en base64 à partir de l'URI TOTP."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode()


def verify_totp(secret: str, token: str, window: int = 1) -> bool:
    """Vérifie si le token TOTP est valide (avec tolérance temporelle)."""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=window)


def consume_backup_code(user, code: str) -> bool:
    """Consomme un code de secours MFA (usage unique)."""
    import json
    raw = user.mfa_backup_codes or '[]'
    try:
        codes = json.loads(raw) if isinstance(raw, str) else list(raw)
    except (json.JSONDecodeError, TypeError):
        codes = []
    normalized = code.strip().replace('-', '').lower()
    for index, stored in enumerate(codes):
        if stored.replace('-', '').lower() == normalized:
            codes.pop(index)
            user.mfa_backup_codes = json.dumps(codes)
            user.save(update_fields=['mfa_backup_codes'])
            return True
    return False


def verify_mfa_login(user, token: str) -> bool:
    """Vérifie TOTP ou code de secours pour la connexion MFA."""
    if user.mfa_secret and verify_totp(user.mfa_secret, token):
        return True
    return consume_backup_code(user, token)


def get_backup_codes(count: int = 10) -> list:
    """Génère des codes de secours (backup codes) en cas de perte du device TOTP."""
    import secrets
    return [secrets.token_hex(4) for _ in range(count)]
