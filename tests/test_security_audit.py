"""Tests sécurité : lits atomiques, immuabilité LIS, pagination, MFA, concurrence."""
import pytest
from django.contrib.auth import get_user_model

from clinical.models import Patient, Consultation
from clinical.services import creer_admission, HospitalisationError
from hospital_structure.models import Lit, ServiceHospitalier
from laboratory.models import DemandeExamen, ResultatExamen, ExamenType
from laboratory.services import creer_demande

User = get_user_model()


@pytest.fixture
def medecin_user(db):
    return User.objects.create_user(
        username='med_audit', password='TestPass123!', role='MEDECIN',
        email='med.audit@gmail.com', matricule='MEDAUD',
    )


@pytest.fixture
def biologiste_user(db):
    return User.objects.create_user(
        username='bio_audit', password='TestPass123!', role='BIOLOGISTE',
        email='bio.audit@gmail.com', matricule='BIOAUD',
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='admin_audit', password='TestPass123!', role='ADMIN',
        email='admin.audit@gmail.com', matricule='ADMAUD', is_superuser=True,
    )


@pytest.fixture
def patient_demo(db, medecin_user):
    user = User.objects.create_user(
        username='pat_audit', password='TestPass123!', role='PATIENT',
        email='pat.audit@gmail.com',
    )
    return Patient.objects.create(
        utilisateur=user, nom='Test', prenom='Patient',
        date_naissance='1990-01-01', telephone='+243900000099',
        consentement_donnees=True,
    )


@pytest.mark.django_db
def test_lit_occuper_atomique_bloque_double_occupation(patient_demo, medecin_user):
    service = ServiceHospitalier.objects.filter(est_actif=True).first()
    lit = Lit.objects.filter(chambre__service=service, statut='LIBRE').first()
    assert lit is not None

    creer_admission(
        patient_id=patient_demo.id,
        service_id=service.id,
        lit_id=lit.id,
        medecin_referent_id=medecin_user.id,
        motif_hospitalisation='Test concurrence',
        date_previsionnelle_sortie='2026-12-31',
        lit_version=lit.version,
    )

    user2 = User.objects.create_user(
        username='pat_audit2', password='TestPass123!', role='PATIENT',
        email='pat2.audit@gmail.com',
    )
    patient2 = Patient.objects.create(
        utilisateur=user2, nom='Deux', prenom='Patient',
        date_naissance='1991-01-01', telephone='+243900000098',
        consentement_donnees=True,
    )

    with pytest.raises(HospitalisationError):
        creer_admission(
            patient_id=patient2.id,
            service_id=service.id,
            lit_id=lit.id,
            medecin_referent_id=medecin_user.id,
            motif_hospitalisation='Tentative double',
            date_previsionnelle_sortie='2026-12-31',
        )


@pytest.mark.django_db
def test_admission_sortie_conflit_version_409(api_client, patient_demo, medecin_user):
    service = ServiceHospitalier.objects.filter(est_actif=True).first()
    lit = Lit.objects.filter(chambre__service=service, statut='LIBRE').first()
    admission = creer_admission(
        patient_id=patient_demo.id,
        service_id=service.id,
        lit_id=lit.id,
        medecin_referent_id=medecin_user.id,
        motif_hospitalisation='Test version',
        date_previsionnelle_sortie='2026-12-31',
    )
    token = _jwt(medecin_user)
    response = api_client.post(
        f'/api/v1/clinical/admissions/{admission.id}/sortie',
        data={'statut': 'SORTI', 'notes': '', 'version': 9999},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 409


@pytest.mark.django_db
def test_resultat_valide_modification_interdite_403(api_client, biologiste_user):
    from datetime import date

    patient = Patient.objects.create(
        nom='Immu', prenom='Test', date_naissance=date(1985, 5, 5),
        telephone='+243900000097', consentement_donnees=True,
    )
    medecin = User.objects.create_user(
        username='med_immu', password='TestPass123!', role='MEDECIN',
        email='med.immu@gmail.com',
    )
    service = ServiceHospitalier.objects.first()
    consult = Consultation.objects.create(
        patient=patient, medecin=medecin, service=service,
        motif='Test', est_terminee=True,
    )
    examen, _ = ExamenType.objects.get_or_create(
        code='TSTAUD', defaults={'nom': 'Test Audit', 'prix': 5000},
    )
    demande = DemandeExamen.objects.create(
        patient=patient, consultation=consult, examen_type=examen,
        medecin_prescripteur=medecin, statut='VALIDATION',
    )
    resultat = ResultatExamen.objects.create(
        demande=demande, resultats='{"ok": 1}', interpretation='OK',
        saisie_par=biologiste_user, est_valide=True,
    )

    token = _jwt(biologiste_user)
    response = api_client.put(
        f'/api/v1/laboratory/resultats/{resultat.id}',
        data={'resultats': '{"hack": true}', 'interpretation': 'hack'},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_patients_list_paginated(api_client, medecin_user):
    token = _jwt(medecin_user)
    response = api_client.get(
        '/api/v1/clinical/patients?page=1&page_size=10',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    data = response.json()
    assert 'items' in data
    assert 'pagination' in data
    assert data['pagination']['page'] == 1


@pytest.mark.django_db
def test_medecins_and_lits_paginated(api_client, admin_user):
    token = _jwt(admin_user)
    for path in ('/api/v1/auth/medecins?page=1', '/api/v1/hospital/lits?page=1'):
        response = api_client.get(path, HTTP_AUTHORIZATION=f'Bearer {token}')
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert 'pagination' in data


@pytest.mark.django_db
def test_uploads_list_paginated(api_client, medecin_user):
    token = _jwt(medecin_user)
    response = api_client.get(
        '/api/v1/files/uploads?page=1&page_size=10',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    data = response.json()
    assert 'items' in data
    assert 'pagination' in data


@pytest.mark.django_db
def test_lis_creer_demande_service(patient_demo, medecin_user):
    service = ServiceHospitalier.objects.filter(est_actif=True).first()
    consult = Consultation.objects.create(
        patient=patient_demo, medecin=medecin_user, service=service,
        motif='Consultation LIS', est_terminee=True,
    )
    examen, _ = ExamenType.objects.get_or_create(
        code='LISRV', defaults={'nom': 'LIS Service', 'prix': 3000},
    )
    demande = creer_demande(
        patient_id=patient_demo.id,
        medecin_prescripteur_id=medecin_user.id,
        consultation_id=consult.id,
        examen_type_id=examen.id,
    )
    assert demande.statut == 'PRESCRIT'
    assert demande.patient_id == patient_demo.id


@pytest.mark.django_db
def test_mfa_backup_code_login(api_client, db):
    import json
    from authentication import mfa

    user = User.objects.create_user(
        username='mfa_backup', password='TestPass123!', role='ADMIN',
        email='mfa.backup@gmail.com',
    )
    user.is_mfa_enabled = True
    user.mfa_secret = mfa.generate_totp_secret(user.id)
    user.mfa_backup_codes = json.dumps(['abcd1234', 'efgh5678'])
    user.save()

    login_resp = api_client.post(
        '/api/v1/auth/login',
        data={'username': 'mfa_backup', 'password': 'TestPass123!'},
        content_type='application/json',
    )
    assert login_resp.status_code == 200
    mfa_session = login_resp.json()['mfa_session']

    mfa_resp = api_client.post(
        '/api/v1/auth/login/mfa',
        data={'mfa_session': mfa_session, 'totp_token': 'abcd1234'},
        content_type='application/json',
    )
    assert mfa_resp.status_code == 200
    assert mfa_resp.json().get('token')

    user.refresh_from_db()
    codes = json.loads(user.mfa_backup_codes)
    assert 'abcd1234' not in codes


@pytest.mark.django_db
def test_account_lockout_after_five_failed_attempts(api_client, db):
    User.objects.create_user(
        username='lockout_user', password='TestPass123!', role='PATIENT',
        email='lockout.user@gmail.com',
    )

    for _ in range(5):
        resp = api_client.post(
            '/api/v1/auth/login',
            data={'username': 'lockout_user', 'password': 'wrong-password'},
            content_type='application/json',
        )
        assert resp.status_code == 401

    locked_resp = api_client.post(
        '/api/v1/auth/login',
        data={'username': 'lockout_user', 'password': 'wrong-password'},
        content_type='application/json',
    )
    assert locked_resp.status_code == 423
    assert 'verrouillé' in locked_resp.json()['error'].lower()

    user = User.objects.get(username='lockout_user')
    assert user.failed_login_attempts >= 5
    assert user.lockout_until is not None


@pytest.mark.django_db
def test_account_lockout_cleared_on_success(api_client, db):
    user = User.objects.create_user(
        username='unlock_user', password='TestPass123!', role='PATIENT',
        email='unlock.user@gmail.com',
    )
    user.failed_login_attempts = 3
    user.save(update_fields=['failed_login_attempts'])

    resp = api_client.post(
        '/api/v1/auth/login',
        data={'username': 'unlock_user', 'password': 'TestPass123!'},
        content_type='application/json',
    )
    assert resp.status_code == 200

    user.refresh_from_db()
    assert user.failed_login_attempts == 0
    assert user.lockout_until is None


@pytest.mark.django_db
def test_login_rate_limit_uses_ip_and_username(api_client, db):
    from django.core.cache import cache

    cache.clear()
    User.objects.create_user(
        username='ratelimit_user', password='TestPass123!', role='PATIENT',
        email='ratelimit.user@gmail.com',
    )

    for _ in range(10):
        resp = api_client.post(
            '/api/v1/auth/login',
            data={'username': 'ratelimit_user', 'password': 'wrong-password'},
            content_type='application/json',
        )
        assert resp.status_code in (401, 423)

    blocked = api_client.post(
        '/api/v1/auth/login',
        data={'username': 'ratelimit_user', 'password': 'wrong-password'},
        content_type='application/json',
    )
    assert blocked.status_code == 429


def _jwt(user):
    import jwt
    from django.conf import settings
    from datetime import datetime, timedelta
    payload = {
        'id': user.id, 'username': user.username, 'role': user.role,
        'email': user.email, 'exp': datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
