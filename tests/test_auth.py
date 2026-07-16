import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='admin_test',
        password='TestPass123!',
        role='ADMIN',
        first_name='Admin',
        last_name='Test',
    )


@pytest.mark.django_db
def test_login_invalid_credentials(api_client):
    response = api_client.post(
        '/api/v1/auth/login',
        data={'username': 'nobody', 'password': 'wrong'},
        content_type='application/json',
    )
    assert response.status_code in (401, 422, 400)


@pytest.mark.django_db
@override_settings(EMAIL_OTP_ENABLED=False)
def test_login_success(api_client, admin_user):
    response = api_client.post(
        '/api/v1/auth/login',
        data={'username': 'admin_test', 'password': 'TestPass123!'},
        content_type='application/json',
    )
    assert response.status_code == 200
    data = response.json()
    assert 'token' in data
    assert data['user']['role'] == 'ADMIN'
