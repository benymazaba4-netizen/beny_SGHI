import pytest

from common.encryption import decrypt_value, encrypt_value


def test_encrypt_decrypt_roundtrip():
    plain = 'donnee-medicale-sensible'
    cipher = encrypt_value(plain)
    assert cipher != plain
    assert decrypt_value(cipher) == plain


def test_encrypt_empty():
    assert encrypt_value('') == ''
    assert decrypt_value('') == ''


@pytest.mark.django_db
def test_patient_sensitive_fields_encrypted():
    from datetime import date
    from clinical.models import Patient

    p = Patient.objects.create(
        nom='Encrypt', prenom='Test', date_naissance=date(1990, 1, 1),
        telephone='000', adresse='x', numero_identite_national='ID-12345',
        numero_securite_sociale='SS-999',
    )
    assert p.numero_identite_national.startswith('gAAAA')
    assert decrypt_value(p.numero_identite_national) == 'ID-12345'
