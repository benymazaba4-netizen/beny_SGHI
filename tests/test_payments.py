import jwt
import pytest
from datetime import date, timedelta, datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model

from clinical.models import Patient
from billing.models import Facture, EcheancePaiement

User = get_user_model()


def _token(user, patient_id=None):
    payload = {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'email': user.email or '',
        'exp': datetime.utcnow() + timedelta(hours=1),
    }
    if patient_id:
        payload['patient_id'] = patient_id
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


@pytest.fixture
def patient_user(db):
    user = User.objects.create_user(username='pay_pat', password='TestPass123!', role='PATIENT')
    patient = Patient.objects.create(
        nom='Pay', prenom='Patient', date_naissance=date(1990, 1, 1),
        telephone='+243900000010', adresse='Test', consentement_donnees=True,
        utilisateur=user,
    )
    return user, patient


@pytest.mark.django_db
def test_patient_paiement_partiel(client, patient_user):
    user, patient = patient_user
    facture = Facture.objects.create(
        patient=patient, statut='EMISE',
        sous_total=Decimal('100000'), montant_patient=Decimal('100000'),
        montant_restant=Decimal('100000'),
    )
    token = _token(user, patient.id)
    res = client.post(
        '/api/v1/billing/paiements/mobile-money',
        data={
            'facture_id': facture.id,
            'mode_paiement': 'MTN',
            'montant': '40000',
            'numero_telephone': '+243990000000',
            'operateur': 'MTN',
        },
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert res.status_code == 200
    facture.refresh_from_db()
    assert facture.statut == 'PARTIELLE'
    assert facture.montant_paye == Decimal('40000')
    assert facture.montant_restant == Decimal('60000')


@pytest.mark.django_db
def test_echeancier_facture(client, patient_user):
    user, patient = patient_user
    admin = User.objects.create_user(username='pay_admin', password='TestPass123!', role='ADMIN')
    facture = Facture.objects.create(
        patient=patient, statut='EMISE',
        sous_total=Decimal('80000'), montant_patient=Decimal('80000'),
        montant_restant=Decimal('80000'),
    )
    token = _token(admin)
    res = client.post(
        f'/api/v1/billing/factures/{facture.id}/echeancier',
        data={
            'echeances': [
                {'date_echeance': str(date.today() + timedelta(days=30)), 'montant': '40000'},
                {'date_echeance': str(date.today() + timedelta(days=60)), 'montant': '40000'},
            ],
        },
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert res.status_code == 201
    assert EcheancePaiement.objects.filter(facture=facture).count() == 2
