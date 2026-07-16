"""Tests rappels rendez-vous par e-mail."""

from datetime import timedelta

import pytest
from django.core import mail
from django.test import override_settings
from django.utils import timezone

from appointments.models import RendezVous
from authentication.models import Utilisateur
from clinical.models import Patient
from hospital_structure.models import Batiment, ServiceHospitalier
from notifications.services import envoyer_rappels_rdv


@pytest.fixture
def rdv_demain(db):
    medecin = Utilisateur.objects.create_user(
        username='med_rappel',
        password='TestPass123!',
        role='MEDECIN',
        first_name='Anne',
        last_name='Dupont',
    )
    user = Utilisateur.objects.create_user(
        username='patient_rappel',
        password='TestPass123!',
        role='PATIENT',
        email='patient.rappel@example.com',
    )
    patient = Patient.objects.create(
        nom='Kabila',
        prenom='Marie',
        date_naissance='1990-01-01',
        telephone='+243900000001',
        adresse='Kinshasa',
        email='patient.rappel@example.com',
        utilisateur=user,
        consentement_donnees=True,
    )
    bat = Batiment.objects.create(nom='Bloc B', code='BB', adresse='CHU')
    service = ServiceHospitalier.objects.create(nom='Cardiologie', code='CARD', batiment=bat)
    date_rdv = timezone.now() + timedelta(hours=24)
    rdv = RendezVous.objects.create(
        patient=patient,
        medecin=medecin,
        service=service,
        date_heure=date_rdv,
        motif='Suivi cardiologique',
        statut='CONFIRME',
    )
    return rdv


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    RDV_REMINDER_HOURS=24,
    RDV_REMINDER_WINDOW_HOURS=2,
)
def test_envoyer_rappels_rdv_email_et_notification(rdv_demain):
    stats = envoyer_rappels_rdv()

    assert stats['traites'] == 1
    assert stats['emails'] == 1
    assert stats['notifications'] == 1
    assert len(mail.outbox) == 1
    assert 'Rappel RDV demain' in mail.outbox[0].subject
    assert 'Suivi cardiologique' in mail.outbox[0].body

    rdv_demain.refresh_from_db()
    assert rdv_demain.rappel_envoye is True


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    RDV_REMINDER_HOURS=24,
    RDV_REMINDER_WINDOW_HOURS=1,
)
def test_envoyer_rappels_rdv_idempotent(rdv_demain):
    envoyer_rappels_rdv()
    stats = envoyer_rappels_rdv()
    assert stats['traites'] == 0
    assert len(mail.outbox) == 1
