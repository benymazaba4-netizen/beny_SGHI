import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import override_settings

from authentication.otp_service import OTP_EMAIL_ERROR

User = get_user_model()

OTP_SETTINGS = {
    'EMAIL_OTP_ENABLED': True,
    'EMAIL_BACKEND': 'django.core.mail.backends.locmem.EmailBackend',
    'EMAIL_USE_REAL_SMTP': False,
    'DEFAULT_FROM_EMAIL': 'noreply@sghi.local',
    'EMAIL_HOST_USER': 'noreply@sghi.local',
    'CACHES': {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    },
}


@pytest.fixture(autouse=True)
def clear_otp_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
@override_settings(**OTP_SETTINGS)
def test_login_staff_otp_sent_to_user_email(api_client):
    User.objects.create_user(
        username='medecin_otp',
        password='TestPass123!',
        role='MEDECIN',
        email='medecin.pro@outlook.com',
    )

    response = api_client.post(
        '/api/v1/auth/login',
        data={'username': 'medecin_otp', 'password': 'TestPass123!'},
        content_type='application/json',
    )
    assert response.status_code == 200
    data = response.json()
    assert data['otp_required'] is True
    assert data['token'] is None
    assert data['otp_session']
    assert data['otp_email_hint'].endswith('@outlook.com')

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ['medecin.pro@outlook.com']
    assert 'SGHI ERP' in mail.outbox[0].subject
    assert 'Votre code OTP est :' in mail.outbox[0].body

    cached = cache.get(f"otp_login_{data['otp_session']}")
    code = cached['code']

    otp_response = api_client.post(
        '/api/v1/auth/login/otp',
        data={'otp_session': data['otp_session'], 'otp_code': code},
        content_type='application/json',
    )
    assert otp_response.status_code == 200
    assert otp_response.json()['token']
    assert otp_response.json()['user']['role'] == 'MEDECIN'


@pytest.mark.django_db
@override_settings(**OTP_SETTINGS)
def test_login_patient_otp_sent_to_personal_email(api_client):
    User.objects.create_user(
        username='patient_otp',
        password='TestPass123!',
        role='PATIENT',
        email='patient.perso@yahoo.fr',
    )

    response = api_client.post(
        '/api/v1/auth/login',
        data={'username': 'patient_otp', 'password': 'TestPass123!'},
        content_type='application/json',
    )
    assert response.status_code == 200
    data = response.json()
    assert data['otp_required'] is True

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ['patient.perso@yahoo.fr']

    cached = cache.get(f"otp_login_{data['otp_session']}")
    code = cached['code']

    otp_response = api_client.post(
        '/api/v1/auth/login/otp',
        data={'otp_session': data['otp_session'], 'otp_code': code},
        content_type='application/json',
    )
    assert otp_response.status_code == 200
    assert otp_response.json()['user']['role'] == 'PATIENT'


@pytest.mark.django_db
@override_settings(**OTP_SETTINGS, OTP_ALLOW_BYPASS=True, DEBUG=False)
def test_demo_mode_exposes_otp_without_sending_email(api_client):
    User.objects.create_user(
        username='jury_demo',
        password='TestPass123!',
        role='PATIENT',
        email='jury@example.com',
    )

    response = api_client.post(
        '/api/v1/auth/login',
        data={'username': 'jury_demo', 'password': 'TestPass123!'},
        content_type='application/json',
    )

    assert response.status_code == 200
    data = response.json()
    assert data['otp_required'] is True
    assert data['demo_otp_code'].isdigit()
    assert len(data['demo_otp_code']) == 6
    assert len(mail.outbox) == 0

    otp_response = api_client.post(
        '/api/v1/auth/verify-otp',
        data={'username': 'jury_demo', 'otp_code': data['demo_otp_code']},
        content_type='application/json',
    )
    assert otp_response.status_code == 200
    assert otp_response.json()['token']


@pytest.mark.django_db
@override_settings(**OTP_SETTINGS, DEBUG=True)
def test_verify_otp_with_username(api_client):
    User.objects.create_user(
        username='secretaire_otp',
        password='TestPass123!',
        role='SECRETAIRE',
        email='secretaire@entreprise-hospitaliere.fr',
    )

    response = api_client.post(
        '/api/v1/auth/login',
        data={'username': 'secretaire_otp', 'password': 'TestPass123!'},
        content_type='application/json',
    )
    assert response.status_code == 200
    data = response.json()
    assert data['otp_required'] is True
    assert mail.outbox[0].to == ['secretaire@entreprise-hospitaliere.fr']

    cached = cache.get(f"otp_login_{data['otp_session']}")
    code = cached['code']

    otp_response = api_client.post(
        '/api/v1/auth/verify-otp',
        data={'username': 'secretaire_otp', 'otp_code': code},
        content_type='application/json',
    )
    assert otp_response.status_code == 200
    assert otp_response.json()['token']
    assert otp_response.json()['user']['role'] == 'SECRETAIRE'


@pytest.mark.django_db
@override_settings(**OTP_SETTINGS)
def test_login_without_email_returns_400(api_client):
    User.objects.create_user(
        username='sans_email',
        password='TestPass123!',
        role='ADMIN',
        email='',
    )

    response = api_client.post(
        '/api/v1/auth/login',
        data={'username': 'sans_email', 'password': 'TestPass123!'},
        content_type='application/json',
    )
    assert response.status_code == 400
    assert response.json()['error'] == OTP_EMAIL_ERROR
    assert len(mail.outbox) == 0


@pytest.mark.django_db
@override_settings(**OTP_SETTINGS)
def test_resend_login_otp(api_client):
    User.objects.create_user(
        username='patient_resend',
        password='TestPass123!',
        role='PATIENT',
        email='resend@gmail.com',
    )

    response = api_client.post(
        '/api/v1/auth/login',
        data={'username': 'patient_resend', 'password': 'TestPass123!'},
        content_type='application/json',
    )
    session_id = response.json()['otp_session']
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ['resend@gmail.com']

    resend = api_client.post(
        '/api/v1/auth/login/otp/resend',
        data={'otp_session': session_id},
        content_type='application/json',
    )
    assert resend.status_code == 200
    assert len(mail.outbox) == 2
    assert mail.outbox[1].to == ['resend@gmail.com']

    cached = cache.get(f"otp_login_{session_id}")
    code = cached['code']

    otp_response = api_client.post(
        '/api/v1/auth/login/otp',
        data={'otp_session': session_id, 'otp_code': code},
        content_type='application/json',
    )
    assert otp_response.status_code == 200
    assert otp_response.json()['token']
