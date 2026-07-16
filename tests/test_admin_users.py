import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='admin_test',
        password='TestPass123!',
        role='ADMIN',
        email='admin.test@gmail.com',
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def regular_admin_user(db):
    return User.objects.create_user(
        username='admin_regular',
        password='TestPass123!',
        role='ADMIN',
        email='admin.regular@gmail.com',
        is_staff=True,
        is_superuser=False,
    )


@pytest.fixture
def superadmin_target(db):
    return User.objects.create_user(
        username='superadmin_target',
        password='TestPass123!',
        role='ADMIN',
        email='super.target@gmail.com',
        is_staff=True,
        is_superuser=True,
        first_name='Super',
        last_name='Cible',
        matricule='SUPER999',
    )


@pytest.fixture
def target_user(db):
    return User.objects.create_user(
        username='medecin_edit',
        password='TestPass123!',
        role='MEDECIN',
        email='medecin.edit@gmail.com',
        first_name='Jean',
        last_name='Test',
        matricule='MED999',
    )


@pytest.mark.django_db
def test_django_admin_url_disabled_by_default(client):
    response = client.get('/admin/')
    assert response.status_code == 404


@pytest.mark.django_db
def test_django_admin_disabled_in_settings():
    from django.conf import settings
    assert settings.DJANGO_ADMIN_ENABLED is False


@pytest.mark.django_db
def test_admin_can_update_user(api_client, admin_user, target_user):
    token = _login_as(api_client, admin_user)
    response = api_client.patch(
        f'/api/v1/auth/users/{target_user.id}',
        data={
            'first_name': 'Paul',
            'last_name': 'Modifié',
            'email': 'paul.modifie@gmail.com',
            'telephone': '+243900000099',
            'role': 'MEDECIN',
            'is_active': True,
        },
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    data = response.json()
    assert data['first_name'] == 'Paul'
    assert data['email'] == 'paul.modifie@gmail.com'

    target_user.refresh_from_db()
    assert target_user.first_name == 'Paul'
    assert target_user.email == 'paul.modifie@gmail.com'


@pytest.mark.django_db
def test_regular_admin_cannot_update_superadmin(api_client, regular_admin_user, superadmin_target):
    token = _login_as(api_client, regular_admin_user)
    response = api_client.patch(
        f'/api/v1/auth/users/{superadmin_target.id}',
        data={'first_name': 'Hack'},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 403
    assert 'super-administrateur' in response.json()['error'].lower()


@pytest.mark.django_db
def test_superadmin_can_update_superadmin(api_client, admin_user, superadmin_target):
    token = _login_as(api_client, admin_user)
    response = api_client.patch(
        f'/api/v1/auth/users/{superadmin_target.id}',
        data={'first_name': 'SuperModifie'},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    assert response.json()['first_name'] == 'SuperModifie'


def _login_as(api_client, user):
    import jwt
    from django.conf import settings
    from datetime import datetime, timedelta

    payload = {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
