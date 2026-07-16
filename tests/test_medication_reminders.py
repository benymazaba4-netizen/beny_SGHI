import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model

from clinical.models import Patient, Consultation
from hospital_structure.models import ServiceHospitalier
from notifications.models import Notification
from notifications.services import envoyer_rappels_medicaments
from prescriptions.models import Medicament, Prescription, LignePrescription

User = get_user_model()


@pytest.mark.django_db
def test_rappels_medicaments_idempotents():
    user = User.objects.create_user(
        username='pat_med', password='TestPass123!', role='PATIENT',
    )
    patient = Patient.objects.create(
        nom='Med', prenom='Patient', date_naissance=date(1988, 3, 3),
        telephone='+243900000002', adresse='Test', consentement_donnees=True,
        utilisateur=user,
    )
    medecin = User.objects.create_user(username='med_med', password='TestPass123!', role='MEDECIN')
    service = ServiceHospitalier.objects.first()
    if not service:
        from hospital_structure.seed_data import seed_hospital_structure
        seed_hospital_structure()
        service = ServiceHospitalier.objects.first()

    consult = Consultation.objects.create(
        patient=patient, medecin=medecin, service=service,
        motif='Test', diagnostic='Test',
    )
    medicament = Medicament.objects.create(code='RM01', nom='Paracétamol', prix_unitaire=Decimal('50'))
    presc = Prescription.objects.create(
        patient=patient, medecin=medecin, consultation=consult,
        date_debut=date.today(), date_fin=date.today() + timedelta(days=5),
        statut='BROUILLON', est_verrouillee=False,
    )
    LignePrescription.objects.create(
        prescription=presc, medicament=medicament,
        quantite_prescitee=10, frequence='2x/jour', duree_jours=5,
    )
    presc.est_verrouillee = True
    presc.statut = 'VALIDE'
    presc.save(update_fields=['est_verrouillee', 'statut'])

    stats1 = envoyer_rappels_medicaments()
    stats2 = envoyer_rappels_medicaments()

    assert stats1['notifications'] >= 1
    assert stats2['ignorees'] >= 1
    assert Notification.objects.filter(utilisateur=user, type_notification='MEDICAMENT').count() >= 1
