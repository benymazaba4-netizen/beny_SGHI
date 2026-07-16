"""Met a jour l'e-mail du compte tricia pour recevoir les OTP."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from authentication.models import Utilisateur
from authentication.otp_service import create_login_otp
from clinical.models import Patient

EMAIL = 'benymazaba4@gmail.com'
user = Utilisateur.objects.filter(username='tricia', role='PATIENT').first()
if not user:
    print('Compte tricia introuvable')
    sys.exit(1)

user.email = EMAIL
user.save(update_fields=['email'])
patient = Patient.objects.filter(utilisateur=user).first()
if patient:
    patient.email = EMAIL
    patient.save(update_fields=['email'])

sid, hint, err = create_login_otp(user)
print(f'Email mis a jour : {EMAIL}')
print(f'OTP envoye : {bool(sid)} hint={hint} err={err}')
