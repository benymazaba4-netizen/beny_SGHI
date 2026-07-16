"""
MFA endpoints pour setup et vérification TOTP
"""
import json

from django.core.cache import cache
from ninja import Router, Schema

from .models import Utilisateur
from . import mfa
from common.permissions import auth_bearer
from common.audit_utils import audit_log, get_authenticated_user

mfa_router = Router(auth=auth_bearer, tags=["mfa"])


class MFASetupRequest(Schema):
    """Initier le setup MFA (générer secret et QR code)."""
    pass


class MFASetupResponse(Schema):
    secret: str
    qr_code_base64: str
    backup_codes: list


class MFAVerifyRequest(Schema):
    """Vérifier le TOTP pour activer MFA."""
    totp_token: str


class MFAVerifyResponse(Schema):
    message: str
    backup_codes: list


class MFAAuthenticateRequest(Schema):
    """Utiliser MFA lors de la connexion (après le password)."""
    totp_token: str


@mfa_router.post("/setup", response={200: MFASetupResponse, 401: dict, 400: dict})
def mfa_setup(request):
    """Initier le setup MFA — génère secret et QR code pour authenticator app."""
    user = get_authenticated_user(request)
    if not user:
        return 401, {"error": "Non authentifié"}
    
    if user.is_mfa_enabled:
        return 400, {"error": "MFA déjà activée"}
    
    secret = mfa.generate_totp_secret(user.id)
    uri = mfa.get_totp_uri(user.username, secret)
    qr_code = mfa.generate_qr_code_base64(uri)
    backup_codes = mfa.get_backup_codes(10)
    cache.set(f"mfa_pending_{user.id}", secret, 600)
    cache.set(f"mfa_backup_{user.id}", json.dumps(backup_codes), 600)

    return 200, {
        "secret": secret,
        "qr_code_base64": qr_code,
        "backup_codes": backup_codes,
    }


@mfa_router.post("/verify", response={200: MFAVerifyResponse, 401: dict, 400: dict})
def mfa_verify(request, payload: MFAVerifyRequest):
    """Vérifier le TOTP et activer MFA."""
    user = get_authenticated_user(request)
    if not user:
        return 401, {"error": "Non authentifié"}
    
    if user.is_mfa_enabled:
        return 400, {"error": "MFA déjà activée"}
    
    secret = cache.get(f"mfa_pending_{user.id}")
    if not secret:
        return 400, {"error": "Session MFA expirée — relancez la configuration"}

    if not mfa.verify_totp(secret, payload.totp_token):
        return 400, {"error": "Token TOTP invalide"}

    backup_raw = cache.get(f"mfa_backup_{user.id}")
    backup_codes = json.loads(backup_raw) if backup_raw else mfa.get_backup_codes(10)
    
    user.mfa_secret = secret
    user.mfa_backup_codes = json.dumps(backup_codes)
    user.is_mfa_enabled = True
    user.save()
    cache.delete(f"mfa_pending_{user.id}")
    cache.delete(f"mfa_backup_{user.id}")
    audit_log(request, 'UPDATE', user, new_value="MFA activée")

    return 200, {
        "message": "MFA activée avec succès",
        "backup_codes": backup_codes,
    }


@mfa_router.post("/disable", response={200: dict, 401: dict, 403: dict})
def mfa_disable(request, password: str):
    """Désactiver MFA — nécessite la vérification du mot de passe."""
    from django.contrib.auth import authenticate
    
    user = get_authenticated_user(request)
    if not user:
        return 401, {"error": "Non authentifié"}
    
    # Vérifier le mot de passe
    check_user = authenticate(username=user.username, password=password)
    if not check_user:
        return 403, {"error": "Mot de passe invalide"}
    
    if not user.is_mfa_enabled:
        return 403, {"error": "MFA non activée"}
    
    user.is_mfa_enabled = False
    user.mfa_secret = ''
    user.mfa_backup_codes = ''
    user.save()
    
    audit_log(request, 'UPDATE', user, new_value="MFA désactivée")
    
    return 200, {"message": "MFA désactivée"}


@mfa_router.get("/status", response={200: dict, 401: dict})
def mfa_status(request):
    """Vérifier le statut MFA de l'utilisateur actuel."""
    user = get_authenticated_user(request)
    if not user:
        return 401, {"error": "Non authentifié"}
    
    return 200, {
        "mfa_enabled": user.is_mfa_enabled,
        "mfa_verified_at": user.mfa_verified_at.isoformat() if user.mfa_verified_at else None,
    }
