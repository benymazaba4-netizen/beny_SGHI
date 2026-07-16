"""Tests accès patient aux dossiers."""

import pytest
import jwt
from datetime import datetime, timedelta
from django.conf import settings

from clinical.models import Patient
from authentication.models import Utilisateur


@pytest.fixture
def patient_user(db):
    user = Utilisateur.objects.create_user(
        username='testpatient',
        password='TestPass123!',
        role='PATIENT',
        first_name='Jean',
        last_name='Dupont',
    )
    patient = Patient.objects.create(
        nom='Dupont',
        prenom='Jean',
        date_naissance='1990-01-01',
        telephone='+243900000001',
        adresse='Kinshasa',
        utilisateur=user,
        consentement_donnees=True,
    )
    return user, patient


def _token(user, patient_id=None):
    payload = {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(hours=1),
    }
    if patient_id:
        payload['patient_id'] = patient_id
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


@pytest.mark.django_db
def test_patient_can_read_own_consultations(client, patient_user):
    user, patient = patient_user
    token = _token(user, patient.id)
    response = client.get(
        f'/api/v1/clinical/consultations/patient/{patient.id}',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_patient_cannot_read_other_consultations(client, patient_user):
    user, patient = patient_user
    other = Patient.objects.create(
        nom='Autre',
        prenom='Patient',
        date_naissance='1985-05-05',
        telephone='+243900000002',
        adresse='Lubumbashi',
        consentement_donnees=True,
    )
    token = _token(user, patient.id)
    response = client.get(
        f'/api/v1/clinical/consultations/patient/{other.id}',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_cim10_search(client, db):
    from referentials.models import CodeCIM10
    CodeCIM10.objects.create(code='I10', libelle='Hypertension', chapitre='Circulatoire')
    admin = Utilisateur.objects.create_user(username='admin2', password='Admin2026!', role='ADMIN')
    token = _token(admin)
    response = client.get(
        '/api/v1/referentials/cim10?q=Hyper',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    data = response.json()
    items = data['items'] if isinstance(data, dict) and 'items' in data else data
    assert any(c['code'] == 'I10' for c in items)
