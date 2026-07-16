from functools import wraps
from ninja.security import HttpBearer
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model


class AuthBearer(HttpBearer):
    """Authentification JWT via header Authorization: Bearer <token>"""

    def authenticate(self, request, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            request.auth_payload = payload
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


auth_bearer = AuthBearer()


def _get_auth_payload(request):
    if hasattr(request, 'auth_payload') and request.auth_payload:
        return request.auth_payload
    if hasattr(request, 'auth') and isinstance(request.auth, dict):
        return request.auth
    return None


ROLE_ADMIN = 'ADMIN'
ROLE_MEDECIN = 'MEDECIN'
ROLE_INFIRMIER = 'INFIRMIER'
ROLE_BIOLOGISTE = 'BIOLOGISTE'
ROLE_PHARMACIEN = 'PHARMACIEN'
ROLE_PATIENT = 'PATIENT'
ROLE_SECRETAIRE = 'SECRETAIRE'
ROLE_COMPTABLE = 'COMPTABLE'

ROLE_STAFF = [ROLE_ADMIN, ROLE_MEDECIN, ROLE_INFIRMIER, ROLE_SECRETAIRE]
ROLE_CLINICAL = [ROLE_ADMIN, ROLE_MEDECIN, ROLE_INFIRMIER, ROLE_SECRETAIRE, ROLE_BIOLOGISTE]

# Matrice de permissions par ressource (action -> rôles autorisés)
PERMISSION_MATRIX = {
    'patients.read': ROLE_CLINICAL + [ROLE_PATIENT],
    'patients.write': [ROLE_ADMIN, ROLE_SECRETAIRE],
    'consultations.read': ROLE_CLINICAL + [ROLE_PATIENT],
    'consultations.write': [ROLE_MEDECIN, ROLE_ADMIN],
    'prescriptions.read': [ROLE_MEDECIN, ROLE_ADMIN, ROLE_INFIRMIER, ROLE_PHARMACIEN, ROLE_PATIENT],
    'prescriptions.write': [ROLE_MEDECIN, ROLE_ADMIN],
    'appointments.read': [ROLE_MEDECIN, ROLE_SECRETAIRE, ROLE_ADMIN, ROLE_PATIENT],
    'appointments.write': [ROLE_MEDECIN, ROLE_SECRETAIRE, ROLE_ADMIN, ROLE_PATIENT],
    'messaging.read': [ROLE_MEDECIN, ROLE_PATIENT, ROLE_ADMIN],
    'messaging.write': [ROLE_MEDECIN, ROLE_PATIENT, ROLE_ADMIN],
    'governance.read': [ROLE_ADMIN],
    'governance.write': [ROLE_ADMIN],
}


def get_patient_id_for_user(user):
    """Retourne l'ID patient lié à un utilisateur PATIENT."""
    if not user or user.role != ROLE_PATIENT:
        return None
    patient = getattr(user, 'patient', None)
    return patient.id if patient else None


def enforce_patient_scope(request, patient_id):
    """
    Vérifie qu'un patient ne consulte que son propre dossier.
    Retourne None si OK, sinon un tuple (status_code, dict).
    """
    payload = _get_auth_payload(request)
    if not payload:
        return 401, {"error": "Non authentifié"}
    if payload.get('role') == ROLE_PATIENT:
        own_id = payload.get('patient_id') or get_patient_id_for_user(
            get_user_model().objects.filter(id=payload['id']).first()
        )
        if own_id != patient_id:
            return 403, {"error": "Accès refusé à ce dossier patient"}
    return None


def role_required(allowed_roles):
    """Décorateur pour restreindre l'accès selon les rôles JWT."""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            payload = _get_auth_payload(request)
            if not payload:
                return 401, {"error": "Non authentifié"}

            user_role = payload.get('role')
            if user_role not in allowed_roles:
                return 403, {"error": f"Accès refusé. Rôle requis: {allowed_roles}"}

            request.auth_payload = payload
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def permission_required(permission_key):
    """Décorateur basé sur la matrice de permissions."""
    allowed = PERMISSION_MATRIX.get(permission_key, [ROLE_ADMIN])

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            payload = _get_auth_payload(request)
            if not payload:
                return 401, {"error": "Non authentifié"}
            if payload.get('role') not in allowed:
                return 403, {"error": f"Permission requise: {permission_key}"}
            request.auth_payload = payload
            return func(request, *args, **kwargs)
        return wrapper
    return decorator
