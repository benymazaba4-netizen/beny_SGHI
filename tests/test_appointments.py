"""Tests module rendez-vous."""

import pytest
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

from authentication.models import Utilisateur
from clinical.models import Patient
from hospital_structure.models import Batiment, ServiceHospitalier


@pytest.fixture
def medecin(db):
    return Utilisateur.objects.create_user(
        username='medecin_rdv',
        password='TestPass123!',
        role='MEDECIN',
        first_name='Paul',
        last_name='Médecin',
    )


@pytest.fixture
def patient(db):
    user = Utilisateur.objects.create_user(
        username='patient_rdv',
        password='TestPass123!',
        role='PATIENT',
    )
    p = Patient.objects.create(
        nom='Test',
        prenom='Patient',
        date_naissance='1995-03-15',
        telephone='+243900000099',
        adresse='Kinshasa',
        utilisateur=user,
        consentement_donnees=True,
    )
    return user, p


@pytest.fixture
def service(db):
    bat = Batiment.objects.create(nom='Bloc A', code='BA', adresse='CHU')
    return ServiceHospitalier.objects.create(nom='Consultations', code='CONS', batiment=bat)


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
def test_create_rendez_vous(client, medecin, patient, service):
    user, p = patient
    token = _token(user, p.id)
    date_rdv = (timezone.now() + timedelta(days=2)).replace(microsecond=0)
    response = client.post(
        '/api/v1/appointments/rendez-vous',
        data={
            'patient_id': p.id,
            'medecin_id': medecin.id,
            'service_id': service.id,
            'date_heure': date_rdv.isoformat(),
            'motif': 'Consultation de suivi',
        },
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 201
    assert response.json()['statut'] == 'CONFIRME'
