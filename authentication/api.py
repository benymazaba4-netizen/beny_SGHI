from datetime import date, datetime, timedelta
from typing import List

import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from ninja import Router, Schema

from common.audit_utils import audit_login, audit_log
from common.permissions import auth_bearer, role_required, ROLE_ADMIN, ROLE_SECRETAIRE, ROLE_MEDECIN, ROLE_COMPTABLE, ROLE_PATIENT
from .models import Utilisateur
from . import tokens as refresh_tokens

from clinical.models import Patient

router = Router()

JWT_EXPIRATION_HOURS = getattr(settings, 'JWT_EXPIRATION_HOURS', 1)


class LoginSchema(Schema):
    username: str
    password: str


class LoginResponse(Schema):
    token: str | None = None
    refresh_token: str | None = None
    refresh_expires_at: str | None = None
    user: dict | None = None
    mfa_required: bool = False
    mfa_session: str | None = None
    otp_required: bool = False
    otp_session: str | None = None
    otp_email_hint: str | None = None
    demo_otp_code: str | None = None


class MFALoginSchema(Schema):
    mfa_session: str
    totp_token: str


class VerifyOTPSchema(Schema):
    username: str
    otp_code: str


class OTPLoginSchema(Schema):
    otp_session: str
    otp_code: str


class ResendOTPSchema(Schema):
    otp_session: str


class RegisterSchema(Schema):
    username: str
    password: str
    first_name: str
    last_name: str
    email: str = ''
    telephone: str = ''
    adresse: str = ''
    date_naissance: date
    civilite: str = 'M'
    consentement_donnees: bool = True


@router.post("/register", response={201: LoginResponse, 400: dict})
def register(request, payload: RegisterSchema):
    if Utilisateur.objects.filter(username=payload.username).exists():
        return 400, {"error": "Nom d'utilisateur déjà utilisé"}

    if not (payload.email or '').strip():
        return 400, {"error": "L'adresse e-mail est requise pour recevoir les codes OTP"}

    if len(payload.password) < 8:
        return 400, {"error": "Le mot de passe doit contenir au moins 8 caractères"}

    user = Utilisateur(
        username=payload.username,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        telephone=payload.telephone,
        adresse=payload.adresse,
        role='PATIENT',
        is_active=True,
    )
    user.set_password(payload.password)
    user.save()

    patient = Patient.objects.create(
        nom=payload.last_name,
        prenom=payload.first_name,
        date_naissance=payload.date_naissance,
        telephone=payload.telephone,
        adresse=payload.adresse,
        email=payload.email,
        civilite=payload.civilite,
        consentement_donnees=payload.consentement_donnees,
        utilisateur=user,
    )

    audit_log(request, 'CREATE', user, new_value=f"Patient registration {user.username}")
    audit_log(request, 'CREATE', patient, new_value=f"Patient record {patient.numero_dossier}")

    from common.email_utils import notify_patient_registration
    notify_patient_registration(user, patient)

    token = jwt.encode(
        _build_jwt_payload(user),
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    try:
        refresh_raw, refresh_obj = refresh_tokens.create_refresh_token(user, request=request)
    except Exception:
        refresh_raw = None
        refresh_obj = None

    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "telephone": user.telephone,
        "patient_id": patient.id,
    }

    return 201, {
        "token": token,
        "refresh_token": refresh_raw,
        "refresh_expires_at": refresh_obj.expires_at.isoformat() if refresh_obj else None,
        "user": user_data,
    }


@router.post("login", response={200: LoginResponse, 401: dict, 400: dict, 423: dict})
def login(request, payload: LoginSchema):
    from .lockout import check_account_lockout, record_failed_login, clear_failed_login_attempts

    lockout_error = check_account_lockout(payload.username)
    if lockout_error:
        return 423, {"error": lockout_error}

    user = authenticate(username=payload.username, password=payload.password)
    if not user:
        record_failed_login(request, payload.username)
        return 401, {"error": "Identifiants invalides"}

    clear_failed_login_attempts(user)

    if user.is_mfa_enabled:
        import uuid
        from django.core.cache import cache
        session_id = str(uuid.uuid4())
        cache.set(f"mfa_login_{session_id}", user.id, 300)
        return 200, {
            "mfa_required": True,
            "mfa_session": session_id,
            "user": {"username": user.username, "role": user.role},
        }

    otp_enabled = getattr(settings, 'EMAIL_OTP_ENABLED', True)
    if otp_enabled:
        from . import otp_service
        if not otp_service.resolve_user_email(user):
            return 400, {"error": otp_service.OTP_EMAIL_ERROR}
        session_id, email_hint, err = otp_service.create_login_otp(user, request=request)
        if err:
            return 400, {"error": err}
        return 200, {
            "otp_required": True,
            "otp_session": session_id,
            "otp_email_hint": email_hint,
            "demo_otp_code": otp_service.get_demo_otp(session_id),
            "user": {"username": user.username, "role": user.role, "email": user.email},
        }

    return 200, _issue_tokens(request, user)


@router.post("/login/mfa", response={200: LoginResponse, 401: dict, 400: dict})
def login_mfa(request, payload: MFALoginSchema):
    from django.core.cache import cache
    from . import mfa

    user_id = cache.get(f"mfa_login_{payload.mfa_session}")
    if not user_id:
        return 401, {"error": "Session MFA expirée, reconnectez-vous"}

    try:
        user = Utilisateur.objects.get(id=user_id, is_mfa_enabled=True)
    except Utilisateur.DoesNotExist:
        return 401, {"error": "Utilisateur invalide"}

    if not mfa.verify_mfa_login(user, payload.totp_token):
        from .connexion_log import journaliser_connexion
        journaliser_connexion(request, user, reussie=False)
        return 401, {"error": "Code MFA invalide"}

    user.mfa_verified_at = timezone.now()
    user.save(update_fields=['mfa_verified_at'])

    cache.delete(f"mfa_login_{payload.mfa_session}")
    return 200, _issue_tokens(request, user)


@router.post("/verify-otp", response={200: LoginResponse, 401: dict, 400: dict})
def verify_otp(request, payload: VerifyOTPSchema):
    from . import otp_service

    code = (payload.otp_code or '').strip().replace(' ', '')
    if len(code) != 6 or not code.isdigit():
        return 400, {"error": "Le code OTP doit contenir 6 chiffres."}

    user_id, err = otp_service.verify_login_otp_by_identifier(payload.username, code)
    if err:
        return 401, {"error": err}

    try:
        user = Utilisateur.objects.get(id=user_id, is_active=True)
    except Utilisateur.DoesNotExist:
        return 401, {"error": "Utilisateur invalide"}

    return 200, _issue_tokens(request, user)


@router.post("/login/otp", response={200: LoginResponse, 401: dict, 400: dict})
def login_otp(request, payload: OTPLoginSchema):
    from . import otp_service

    user_id, err = otp_service.verify_login_otp(payload.otp_session, payload.otp_code)
    if err:
        return 401, {"error": err}

    try:
        user = Utilisateur.objects.get(id=user_id, is_active=True)
    except Utilisateur.DoesNotExist:
        return 401, {"error": "Utilisateur invalide"}

    return 200, _issue_tokens(request, user)


@router.post("/login/otp/resend", response={200: LoginResponse, 400: dict})
def resend_login_otp(request, payload: ResendOTPSchema):
    from . import otp_service

    session_id, email_hint, err = otp_service.resend_login_otp(payload.otp_session, request=request)
    if err:
        return 400, {"error": err}
    return 200, {
        "otp_required": True,
        "otp_session": session_id,
        "otp_email_hint": email_hint,
        "demo_otp_code": otp_service.get_demo_otp(session_id),
    }


def _build_jwt_payload(user):
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "email": user.email,
        "exp": expiration,
    }
    if user.role == 'PATIENT':
        patient = getattr(user, 'patient', None)
        if patient:
            payload['patient_id'] = patient.id
    return payload


def _session_user_data(user) -> dict:
    data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "telephone": getattr(user, 'telephone', ''),
        "is_superuser": user.is_superuser,
    }
    if user.role == 'PATIENT':
        patient = getattr(user, 'patient', None)
        if patient:
            data['patient_id'] = patient.id
    return data


def _issue_tokens(request, user):
    token = jwt.encode(
        _build_jwt_payload(user),
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    try:
        refresh_raw, refresh_obj = refresh_tokens.create_refresh_token(user, request=request)
        refresh_expires = refresh_obj.expires_at
    except Exception:
        refresh_raw = None
        refresh_expires = None

    Utilisateur.objects.filter(pk=user.pk).update(date_derniere_connexion=timezone.now())
    from .connexion_log import journaliser_connexion
    journaliser_connexion(request, user, reussie=True)
    audit_login(request, user)

    return {
        "token": token,
        "refresh_token": refresh_raw,
        "refresh_expires_at": refresh_expires.isoformat() if refresh_expires else None,
        "user": _session_user_data(user),
        "mfa_required": False,
        "otp_required": False,
    }


class RefreshSchema(Schema):
    refresh_token: str


@router.post("/refresh", response={200: LoginResponse, 401: dict, 400: dict})
def refresh(request, payload: RefreshSchema):
    """Utilise un refresh token valide pour émettre un nouvel access token et rotater le refresh token."""
    try:
        new_raw, new_obj, user = refresh_tokens.rotate_refresh_token(payload.refresh_token, request=request)
    except ValueError as e:
        return 401, {"error": str(e)}

    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    token = jwt.encode(
        _build_jwt_payload(user),
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    return 200, {
        "token": token,
        "refresh_token": new_raw,
        "refresh_expires_at": new_obj.expires_at.isoformat(),
        "user": _session_user_data(user),
    }


class LogoutSchema(Schema):
    refresh_token: str


@router.post("/logout", response={200: dict, 400: dict})
def logout(request, payload: LogoutSchema):
    from common.audit_utils import audit_log, get_authenticated_user
    user = get_authenticated_user(request)
    revoked = refresh_tokens.revoke_refresh_token(payload.refresh_token)
    if not revoked:
        return 400, {"error": "Refresh token invalide"}
    if user:
        audit_log(request, 'LOGOUT', user, new_value='Déconnexion — refresh token révoqué')
    return 200, {"message": "Déconnecté"}


class UserOut(Schema):
    id: int
    username: str
    email: str
    role: str
    first_name: str
    last_name: str
    is_active: bool
    is_superuser: bool = False
    telephone: str = ''
    matricule: str = ''
    date_derniere_connexion: str = ''


class UserUpdateSchema(Schema):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    role: str | None = None
    is_active: bool | None = None
    telephone: str | None = None
    matricule: str | None = None


def _user_to_dict(user: Utilisateur) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email or '',
        "role": user.role,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "telephone": user.telephone or '',
        "matricule": user.matricule or '',
        "date_derniere_connexion": user.date_derniere_connexion.isoformat() if user.date_derniere_connexion else '',
    }


def _get_admin_actor(request) -> Utilisateur | None:
    payload = getattr(request, 'auth_payload', None) or {}
    user_id = payload.get('id')
    if not user_id:
        return None
    try:
        user = Utilisateur.objects.get(id=user_id, is_active=True)
    except Utilisateur.DoesNotExist:
        return None
    if user.role != ROLE_ADMIN:
        return None
    return user


@router.get("/journal-connexions", auth=auth_bearer, response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def journal_connexions(request, username: str = None, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    from .models import JournalConnexion
    qs = JournalConnexion.objects.select_related('utilisateur').order_by('-date_connexion')
    if username:
        qs = qs.filter(utilisateur__username=username)
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=200)
    items = [
        {
            'id': j.id,
            'username': j.utilisateur.username,
            'role': j.utilisateur.role,
            'ip_address': str(j.ip_address or ''),
            'reussie': j.reussie,
            'date_connexion': j.date_connexion.isoformat(),
        }
        for j in rows
    ]
    return 200, paginated_response(items, meta)


@router.get("/users", auth=auth_bearer, response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN])
def list_users(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Utilisateur.objects.all().order_by('role', 'username')
    users, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    return 200, paginated_response([_user_to_dict(u) for u in users], meta)


@router.patch("/users/{user_id}", auth=auth_bearer, response={200: UserOut, 400: dict, 401: dict, 403: dict, 404: dict})
@role_required([ROLE_ADMIN])
def update_user(request, user_id: int, payload: UserUpdateSchema):
    actor = _get_admin_actor(request)
    if not actor:
        return 403, {"error": "Accès refusé"}

    try:
        user = Utilisateur.objects.get(id=user_id)
    except Utilisateur.DoesNotExist:
        return 404, {"error": "Utilisateur introuvable"}

    if user.is_superuser and not actor.is_superuser:
        return 403, {"error": "Seul un super-administrateur peut modifier ce compte."}

    updates = payload.dict(exclude_unset=True)
    if not updates:
        return 400, {"error": "Aucune modification fournie"}

    allowed_system_fields = {'email', 'role', 'is_active'}
    forbidden_fields = set(updates) - allowed_system_fields
    if forbidden_fields:
        return 403, {
            "error": (
                "Accès refusé : l'administrateur ne peut modifier que les accès système, "
                "le rôle et l'activation du compte."
            )
        }

    if updates.get('is_active') is False and user.id == actor.id:
        return 400, {"error": "Vous ne pouvez pas désactiver votre propre compte."}

    valid_roles = {c[0] for c in Utilisateur.ROLE_CHOICES}
    if 'role' in updates:
        if updates['role'] not in valid_roles:
            return 400, {"error": "Rôle invalide"}
        if user.is_superuser and updates['role'] != ROLE_ADMIN:
            return 400, {"error": "Un super-administrateur doit conserver le rôle ADMIN."}

    if 'email' in updates and updates['email'] and '@' not in updates['email']:
        return 400, {"error": "Adresse e-mail invalide"}

    old_value = f"{user.username}|{user.role}|{user.email}|{user.is_active}"

    for field, value in updates.items():
        setattr(user, field, value)
    user.save(update_fields=list(updates.keys()))

    audit_log(
        request, 'UPDATE', user,
        old_value=old_value,
        new_value=f"{user.username}|{user.role}|{user.email}|{user.is_active}",
    )
    return 200, _user_to_dict(user)


@router.get("/medecins", auth=auth_bearer, response={200: dict, 401: dict, 403: dict})
@role_required([ROLE_ADMIN, ROLE_SECRETAIRE, ROLE_MEDECIN, ROLE_COMPTABLE, ROLE_PATIENT])
def list_medecins(request, page: int = 1, page_size: int = 50):
    from common.pagination import paginate_queryset, paginated_response
    qs = Utilisateur.objects.filter(role=ROLE_MEDECIN, is_active=True).order_by('last_name', 'first_name')
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size=100)
    items = [
        {
            "id": m.id,
            "username": m.username,
            "first_name": m.first_name,
            "last_name": m.last_name,
            "email": m.email or '',
        }
        for m in rows
    ]
    return 200, paginated_response(items, meta)
