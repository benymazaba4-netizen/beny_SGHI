import jwt
import pytest
from datetime import date, timedelta, datetime

from django.conf import settings
from django.contrib.auth import get_user_model

from clinical.models import Patient
from governance.models import ArchiveRecord, AnonymizationJob

User = get_user_model()


def _admin_token(user):
    payload = {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'email': user.email or '',
        'exp': datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='admin_gov', password='TestPass123!', role='ADMIN',
    )


@pytest.fixture
def demo_patient(db):
    return Patient.objects.create(
        nom='Gov', prenom='Test', date_naissance=date(1990, 1, 1),
        telephone='+243900000001', adresse='Test', consentement_donnees=True,
    )


@pytest.mark.django_db
def test_archiver_patient(client, admin_user, demo_patient):
    token = _admin_token(admin_user)
    res = client.post(
        f'/api/v1/governance/patients/{demo_patient.id}/archiver',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert res.status_code == 200
    assert ArchiveRecord.objects.filter(object_id=demo_patient.id).exists()


@pytest.mark.django_db
def test_create_anonymisation_job(client, admin_user):
    token = _admin_token(admin_user)
    res = client.post(
        '/api/v1/governance/anonymisation',
        data={
            'nom': 'Export stats Q1',
            'periode_debut': str(date.today() - timedelta(days=90)),
            'periode_fin': str(date.today()),
        },
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert res.status_code == 201
    assert AnonymizationJob.objects.filter(nom='Export stats Q1').exists()
