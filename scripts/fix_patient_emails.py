"""Met a jour les e-mails patient invalides pour les tests OTP."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from authentication.models import Utilisateur
from clinical.models import Patient

FIXES = {
    'patient': 'benymazaba4@gmail.com',
}

for username, email in FIXES.items():
    user = Utilisateur.objects.filter(username=username, role='PATIENT').first()
    if not user:
        continue
    user.email = email
    user.save(update_fields=['email'])
    patient = Patient.objects.filter(utilisateur=user).first()
    if patient:
        patient.email = email
        patient.save(update_fields=['email'])
    print(f'OK {username} -> {email}')
