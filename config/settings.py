"""
Django settings for config project — SGHI ERP Médical
"""

from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    # override=True : .env prime sur les variables deja en memoire (runserver long)
    load_dotenv(BASE_DIR / '.env', override=True)
except ImportError:
    import warnings
    warnings.warn(
        'python-dotenv non installe — le fichier .env est ignore. '
        'Lancez : pip install python-dotenv',
        stacklevel=1,
    )


def env(key, default=None):
    return os.environ.get(key, default)


_DEBUG_RAW = env('DEBUG', 'False')
DEBUG = _DEBUG_RAW.lower() in ('true', '1', 'yes')

_DEV_FALLBACK_SECRET_KEY = 'django-insecure-^!4*1x^k5d6pwyf9zsv!ilohc$sgvw=7wla^msvavc-!*3c%+('
_SECRET_KEY_FROM_ENV = (env('SECRET_KEY') or '').strip()

if _SECRET_KEY_FROM_ENV:
    SECRET_KEY = _SECRET_KEY_FROM_ENV
elif DEBUG:
    SECRET_KEY = _DEV_FALLBACK_SECRET_KEY
else:
    raise ImproperlyConfigured(
        'SECRET_KEY est obligatoire en production. '
        'Définissez la variable d\'environnement SECRET_KEY lorsque DEBUG=False.'
    )

ALLOWED_HOSTS = [
    h.strip() for h in env('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()
]
# Render injecte le hostname public
_render_host = (env('RENDER_EXTERNAL_HOSTNAME') or '').strip()
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)

# Interface Django /admin/ — désactivée par défaut (sécurité). Utiliser l'API + portail SGHI.
DJANGO_ADMIN_ENABLED = env('DJANGO_ADMIN_ENABLED', 'False').lower() in ('true', '1', 'yes')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'authentication',
    'clinical',
    'hospital_structure',
    'prescriptions',
    'laboratory',
    'pharmacy',
    'billing',
    'rh',
    'audit',
    'dashboard',
    'common',
    'appointments',
    'messaging',
    'notifications',
    'referentials',
    'governance',
    'interop',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'common.request_context.RequestContextMiddleware',
    'common.rate_limit.RateLimitMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# --- Base de données ---
# Priorité : DATABASE_URL (Render) > PostgreSQL explicite > SQLite.
_database_url = (env('DATABASE_URL') or '').strip()
if _database_url:
    import dj_database_url

    _ssl = env('DB_SSL_REQUIRE', 'True').lower() in ('true', '1', 'yes')
    try:
        _db_cfg = dj_database_url.config(
            default=_database_url,
            conn_max_age=int(env('DB_CONN_MAX_AGE', '60')),
            ssl_require=_ssl,
        )
    except TypeError:
        # Anciennes/nouvelles versions de dj-database-url
        _db_cfg = dj_database_url.config(
            default=_database_url,
            conn_max_age=int(env('DB_CONN_MAX_AGE', '60')),
        )
        if _ssl:
            _db_cfg.setdefault('OPTIONS', {})
            _db_cfg['OPTIONS']['sslmode'] = 'require'
    DATABASES = {'default': _db_cfg}
else:
    # Dev local : SQLite (DB_ENGINE=sqlite ou DB_HOST absent).
    # Production hors Render : PostgreSQL (DB_ENGINE=postgresql + DB_HOST défini).
    _db_engine = (env('DB_ENGINE') or '').strip().lower()
    if not _db_engine:
        _db_engine = 'postgresql' if env('DB_HOST') else 'sqlite'

    if _db_engine == 'postgresql' and env('DB_HOST'):
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': env('DB_NAME', 'sghi_db'),
                'USER': env('DB_USER', 'postgres'),
                'PASSWORD': env('DB_PASSWORD', ''),
                'HOST': env('DB_HOST', 'localhost'),
                'PORT': env('DB_PORT', '5432'),
                'CONN_MAX_AGE': int(env('DB_CONN_MAX_AGE', '60')),
                'OPTIONS': {
                    'connect_timeout': int(env('DB_CONNECT_TIMEOUT', '10')),
                },
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Brazzaville'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        # CompressedStaticFilesStorage évite les erreurs de manifeste au 1er deploy
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

AUTH_USER_MODEL = 'authentication.Utilisateur'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in env(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5180,http://127.0.0.1:5180',
    ).split(',')
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True
# En dev : autoriser tout port localhost (Flutter web, Vite, etc.)
if DEBUG:
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r'^http://localhost:\d+$',
        r'^http://127\.0\.0\.1:\d+$',
    ]

# CSRF — origines de confiance (Render + front)
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in env('CSRF_TRUSTED_ORIGINS', '').split(',')
    if o.strip() and '*' not in o
]
_render_url = (env('RENDER_EXTERNAL_URL') or '').strip().rstrip('/')
if _render_url and _render_url not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(_render_url)
# Ajouter aussi les origines CORS HTTPS en production
for _origin in CORS_ALLOWED_ORIGINS:
    if _origin.startswith('https://') and _origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_origin)

# Derrière le proxy TLS de Render
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

JWT_EXPIRATION_HOURS = int(env('JWT_EXPIRATION_HOURS', '1'))
REFRESH_TOKEN_DAYS = int(env('REFRESH_TOKEN_DAYS', '30'))

ACCOUNT_LOCKOUT_MAX_ATTEMPTS = int(env('ACCOUNT_LOCKOUT_MAX_ATTEMPTS', '5'))
ACCOUNT_LOCKOUT_MINUTES = int(env('ACCOUNT_LOCKOUT_MINUTES', '15'))

# HTTPS & Sécurité
SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1', 'yes')
SESSION_COOKIE_SECURE = env('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
SECURE_HSTS_SECONDS = int(env('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() in ('true', '1', 'yes')

# Cache Redis (production) ou fichier (dev) — fiable pour OTP entre reloads runserver
REDIS_URL = env('REDIS_URL', '')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
else:
    _cache_dir = BASE_DIR / '.cache' / 'django'
    _cache_dir.mkdir(parents=True, exist_ok=True)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': str(_cache_dir),
        }
    }

# Chiffrement AES-256 (données sensibles au repos)
FIELD_ENCRYPTION_KEY = env('FIELD_ENCRYPTION_KEY', SECRET_KEY[:32].ljust(32, '0'))

# --- Configuration des uploads ---
# Limites de taille (octets)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20 MB

# Contrôle de la taille globale
DATA_UPLOAD_MAX_MEMORY_SIZE = int(env('DATA_UPLOAD_MAX_MEMORY_SIZE', str(50 * 1024 * 1024)))  # 50 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = int(env('FILE_UPLOAD_MAX_MEMORY_SIZE', str(50 * 1024 * 1024)))  # 50 MB

# Types MIME autorisés
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
ALLOWED_IMAGE_MIMES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']

ALLOWED_DOCUMENT_EXTENSIONS = ['pdf', 'doc', 'docx', 'xls', 'xlsx']
ALLOWED_DOCUMENT_MIMES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
]

# Stockage des uploads
UPLOADS_DIRECTORY = env('UPLOADS_DIRECTORY', 'uploads')
UPLOADS_TEMP_DIRECTORY = os.path.join(MEDIA_ROOT, '.tmp')

EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = env('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(env('EMAIL_PORT', '587'))
EMAIL_USE_TLS = env('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_USE_SSL = env('EMAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', 'benymazaba4@gmail.com')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')
EMAIL_TIMEOUT = int(env('EMAIL_TIMEOUT', '30'))
DEFAULT_FROM_EMAIL = env(
    'DEFAULT_FROM_EMAIL',
    'Django_SGHI <benymazaba4@gmail.com>',
)

# Envoi réel (Gmail, etc.) — activé si identifiants SMTP renseignés ou forcé dans .env
_email_real_env = env('EMAIL_USE_REAL_SMTP', '')
EMAIL_USE_REAL_SMTP = (
    _email_real_env.lower() in ('true', '1', 'yes')
    if _email_real_env
    else (
        EMAIL_HOST not in ('127.0.0.1', 'localhost', 'mailpit')
        and bool(EMAIL_HOST_USER)
        and bool(EMAIL_HOST_PASSWORD)
    )
)

# OTP par e-mail à la connexion — toujours envoyé à user.email (dynamique)
EMAIL_OTP_ENABLED = env('EMAIL_OTP_ENABLED', 'True').lower() in ('true', '1', 'yes')
STAFF_OTP_EMAIL = env('STAFF_OTP_EMAIL', '')  # legacy, non utilisé pour l'envoi OTP
OTP_EXPIRY_SECONDS = int(env('OTP_EXPIRY_SECONDS', '600'))
OTP_MAX_RESENDS = int(env('OTP_MAX_RESENDS', '3'))
OTP_DEV_BYPASS_CODE = env('OTP_DEV_BYPASS_CODE', '123456')
# True sur Render Free : autorise le code OTP_DEV_BYPASS_CODE (SMTP bloque)
OTP_ALLOW_BYPASS = env('OTP_ALLOW_BYPASS', 'False').lower() in ('true', '1', 'yes')

# Brevo (Sendinblue) — envoi HTTPS, compatible Render Free (SMTP bloque)
BREVO_API_KEY = env('BREVO_API_KEY', '')
BREVO_SENDER_EMAIL = env('BREVO_SENDER_EMAIL', '')
BREVO_SENDER_NAME = env('BREVO_SENDER_NAME', 'SGHI ERP')

RDV_REMINDER_HOURS = int(env('RDV_REMINDER_HOURS', '24'))
RDV_REMINDER_WINDOW_HOURS = int(env('RDV_REMINDER_WINDOW_HOURS', '1'))

# Notifications push FCM (optionnel — configurer FCM_SERVER_KEY en production)
FCM_SERVER_KEY = env('FCM_SERVER_KEY', '')

# Scan antivirus uploads (ClamAV — optionnel)
CLAMAV_ENABLED = env('CLAMAV_ENABLED', 'False').lower() in ('true', '1', 'yes')
CLAMAV_SOCKET = env('CLAMAV_SOCKET', '/var/run/clamav/clamd.ctl')

# Politique API versioning
API_VERSION = '1.0.0'
API_DEPRECATION_POLICY = env('API_DEPRECATION_POLICY', '6_months')
