import base64
import io
import json
from datetime import timedelta

import qrcode
from django.conf import settings
from django.core import signing
from django.utils import timezone

from common.encryption import decrypt_value, encrypt_value

PATIENT_QR_SALT = 'sghi.patient.qr.access.v1'
PATIENT_QR_TTL_SECONDS = int(getattr(settings, 'PATIENT_QR_TTL_SECONDS', 300))


def _access_payload(patient_id: int, generated_by_id: int) -> dict:
    now = timezone.now()
    return {
        'patient_id': patient_id,
        'generated_by_id': generated_by_id,
        'iat': now.isoformat(),
        'exp': (now + timedelta(seconds=PATIENT_QR_TTL_SECONDS)).isoformat(),
        'scope': 'patient.full_record.temporary',
    }


def generate_patient_qr(patient_id: int, generated_by_id: int) -> dict:
    encrypted_payload = encrypt_value(json.dumps(_access_payload(patient_id, generated_by_id), separators=(',', ':')))
    signed_token = signing.dumps({'payload': encrypted_payload}, salt=PATIENT_QR_SALT, compress=True)
    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(signed_token)
    qr.make(fit=True)
    image = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('ascii')
    return {
        'token': signed_token,
        'qr_code_base64': qr_base64,
        'expires_in_seconds': PATIENT_QR_TTL_SECONDS,
        'expires_at': (timezone.now() + timedelta(seconds=PATIENT_QR_TTL_SECONDS)).isoformat(),
    }


def verify_patient_qr_token(token: str) -> dict:
    signed = signing.loads(token, salt=PATIENT_QR_SALT, max_age=PATIENT_QR_TTL_SECONDS)
    decrypted = decrypt_value(signed['payload'])
    data = json.loads(decrypted)
    expires_at = timezone.datetime.fromisoformat(data['exp'])
    if timezone.is_naive(expires_at):
        expires_at = timezone.make_aware(expires_at)
    if timezone.now() > expires_at:
        raise signing.SignatureExpired('Token QR expiré')
    return data
