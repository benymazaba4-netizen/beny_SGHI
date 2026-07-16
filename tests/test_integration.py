import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from clinical.models import Patient, Admission
from clinical.services import creer_admission, HospitalisationError
from hospital_structure.models import Lit, ServiceHospitalier
from prescriptions.models import Medicament, Prescription, LignePrescription
from laboratory.models import DemandeExamen, ExamenType, ResultatExamen

User = get_user_model()


@pytest.fixture
def medecin_user(db):
    return User.objects.create_user(
        username='med_test', password='TestPass123!', role='MEDECIN',
        first_name='Med', last_name='Test',
    )


@pytest.fixture
def demo_patient(db):
    return Patient.objects.create(
        nom='Test', prenom='Patient', date_naissance=date(1985, 5, 5),
        telephone='+243900000099', adresse='Test', consentement_donnees=True,
    )


@pytest.mark.django_db
def test_admission_occupies_lit(medecin_user, demo_patient):
    from hospital_structure.seed_data import seed_hospital_structure
    seed_hospital_structure()
    service = ServiceHospitalier.objects.filter(code='MED-INT').first()
    lit = Lit.objects.filter(chambre__service=service, statut='LIBRE').first()
    assert lit is not None

    admission = creer_admission(
        patient_id=demo_patient.id,
        service_id=service.id,
        lit_id=lit.id,
        medecin_referent_id=medecin_user.id,
        motif_hospitalisation='Test admission',
        date_previsionnelle_sortie=date.today() + timedelta(days=3),
    )
    lit.refresh_from_db()
    assert admission.statut == 'EN_COURS'
    assert lit.statut == 'OCCUPE'

    with pytest.raises(HospitalisationError):
        creer_admission(
            patient_id=demo_patient.id,
            service_id=service.id,
            lit_id=lit.id,
            medecin_referent_id=medecin_user.id,
            motif_hospitalisation='Doublon',
            date_previsionnelle_sortie=date.today() + timedelta(days=1),
        )


@pytest.mark.django_db
def test_prescription_validee_immutable(medecin_user, demo_patient):
    from clinical.models import Consultation
    from hospital_structure.models import ServiceHospitalier
    from prescriptions.models import PrescriptionError

    service = ServiceHospitalier.objects.first()
    if not service:
        from hospital_structure.seed_data import seed_hospital_structure
        seed_hospital_structure()
        service = ServiceHospitalier.objects.first()

    consult = Consultation.objects.create(
        patient=demo_patient, medecin=medecin_user, service=service,
        motif='Test', diagnostic='Test',
    )
    med = Medicament.objects.create(code='TST01', nom='Test Med', prix_unitaire=Decimal('100'))
    presc = Prescription.objects.create(
        patient=demo_patient, medecin=medecin_user, consultation=consult,
        date_debut=date.today(), statut='BROUILLON', est_verrouillee=False,
    )
    LignePrescription.objects.create(
        prescription=presc, medicament=med, quantite_prescitee=10,
        frequence='2x/jour', duree_jours=5,
    )
    presc.statut = 'VALIDE'
    presc.est_verrouillee = True
    presc.save()
    presc.instructions = 'modifié'
    with pytest.raises(PrescriptionError):
        presc.save()


@pytest.mark.django_db
def test_resultat_valide_immutable(medecin_user, demo_patient):
    from clinical.models import Consultation
    from hospital_structure.models import ServiceHospitalier
    from authentication.models import Utilisateur
    from laboratory.models import ResultatExamen

    service = ServiceHospitalier.objects.first()
    if not service:
        from hospital_structure.seed_data import seed_hospital_structure
        seed_hospital_structure()
        service = ServiceHospitalier.objects.first()

    bio = User.objects.create_user(username='bio_test', password='TestPass123!', role='BIOLOGISTE')
    consult = Consultation.objects.create(
        patient=demo_patient, medecin=medecin_user, service=service, motif='Labo',
    )
    examen = ExamenType.objects.create(code='TSTLAB', nom='Test Labo', prix=Decimal('5000'))
    demande = DemandeExamen.objects.create(
        patient=demo_patient, medecin_prescripteur=medecin_user,
        consultation=consult, examen_type=examen, statut='VALIDATION',
    )
    resultat = ResultatExamen.objects.create(
        demande=demande, resultats='{"hb": "14"}', saisie_par=bio, est_valide=True,
    )
    resultat.resultats = 'modifié'
    with pytest.raises(PermissionError):
        resultat.save()
