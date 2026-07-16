# 📧 Guide Système de Notifications Emailings SGHI

## 1. Architecture

### Modèle `EmailLog`
- **Traçabilité immuable** de tous les emails envoyés (audit RGPD)
- **Statuts** : EN_ATTENTE → ENVOYE / ECHEC / REBOND / SPAM
- **Classification** : OTP_LOGIN, RDV_CONFIRMATION, EXAM_PUBLISHED, etc.
- **Indexation** : destinataire, utilisateur, type_email, date_creation

### Fonctionnalités Implémentées

#### ✅ Notifications Existantes
1. **OTP Login** (`notify_otp_login`)
   - Code 6 chiffres envoyé par email
   - Expiration : 10 min (configurable)
   - Staff → email centralisé | Patient → email personnel

2. **RDV Confirmation** (`notify_rdv_confirmation`)
   - Confirmation immédiate après booking
   - Détails : Date, Médecin, Service, Motif

3. **RDV Reminder** (`notify_rdv_reminder`)
   - Rappel 24h avant le rendez-vous
   - Planifié via task cron/Celery

4. **Exam Results** (`notify_exam_published`)
   - Résultat d'examen disponible
   - Lien vers espace patient

5. **Patient Registration** (`notify_patient_registration`)
   - Bienvenue + numéro dossier

#### ✨ **NOUVELLES** Notifications
6. **Prescription Validated** (`notify_prescription_validated`)
   - Validation de prescription
   - Patient → retrait pharmacie

7. **Discharge** (`notify_discharge`)
   - Fin d'hospitalisation
   - Recommandations post-sortie

8. **Invoice Created** (`notify_invoice_created`)
   - Facture disponible
   - Montant total

9. **Medication Reminder** (`notify_medication_reminder`)
   - Rappel prise de médicament
   - Horaires et dosages

---

## 2. Configuration SMTP

### Mode DEV (Mailpit Local)
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=127.0.0.1
EMAIL_PORT=1025
EMAIL_USE_TLS=False
EMAIL_USE_SSL=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=SGHI <noreply@sghi.local>
```

**Accès UI Mailpit** : http://localhost:1080

### Mode PRODUCTION (Gmail)

#### Étape 1 : Activer 2FA sur Gmail
1. Google Account → Security
2. Enable 2-Step Verification

#### Étape 2 : Créer App Password
1. Security → App passwords
2. Select Mail + Windows/Linux
3. Copy password

#### Étape 3 : Configurer .env
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=votre_email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx  # App password (16 chars)
DEFAULT_FROM_EMAIL=SGHI <votre_email@gmail.com>
EMAIL_USE_REAL_SMTP=True
EMAIL_TIMEOUT=30

# Staff OTP centralisé (optionnel)
STAFF_OTP_EMAIL=admin@example.com
OTP_EXPIRY_SECONDS=600
```

#### Étape 4 : Vérifier avec test_email
```bash
python manage.py shell
from common.email_utils import send_notification
send_notification('test@example.com', 'Test', 'Hello!', email_type='OTHER')
```

---

## 3. Usage dans les Applications

### Utiliser une Notification Existante

**Exemple : Confirmation RDV**
```python
from common.email_utils import notify_rdv_confirmation

# Dans appointments/services.py
def confirmer_rdv(rdv):
    rdv.statut = 'CONFIRME'
    rdv.save()
    notify_rdv_confirmation(rdv)  # ✨ Auto-enregistre dans EmailLog
```

### Ajouter Nouvelle Notification
**Exemple : Notification Médicale**
```python
# Dans common/email_utils.py
def notify_lab_alert(patient, alert_msg):
    email = get_patient_email(patient)
    if not email:
        return False
    
    plain = f"Alerte laboratoire : {alert_msg}"
    html = render_email_html("Alerte Laboratoire", [alert_msg])
    
    return send_notification(
        email,
        "Alerte laboratoire",
        plain,
        html_message=html,
        email_type='DOCTOR_ALERT',
        utilisateur=patient.utilisateur,
    )
```

---

## 4. Intégration dans les APIs

### Lors de la Validation de Prescription
```python
# prescriptions/api.py
from common.email_utils import notify_prescription_validated

@router.post("/prescriptions/{id}/valider")
def valider_prescription(request, id: int):
    prescription = get_object_or_404(Prescription, id=id)
    prescription.statut = 'VALIDEE'
    prescription.date_validation = timezone.now()
    prescription.save()
    
    notify_prescription_validated(prescription)  # 📧 Envoyer
    
    return {"status": "ok", "prescription": prescription}
```

### Lors de la Sortie Hospitalière
```python
# clinical/api.py
from common.email_utils import notify_discharge

@router.post("/admissions/{id}/discharge")
def discharge_patient(request, id: int):
    admission = get_object_or_404(Admission, id=id)
    admission.date_sortie = timezone.now()
    admission.statut = 'SORTIE'
    admission.save()
    
    notify_discharge(admission)  # 📧 Envoyer
    
    return {"status": "discharged"}
```

### Lors de la Création de Facture
```python
# billing/api.py
from common.email_utils import notify_invoice_created

@router.post("/factures/generer")
def generer_facture(request, admission_id: int):
    facture = Facture.objects.create(...)
    notify_invoice_created(facture)  # 📧 Envoyer
    return facture
```

---

## 5. Audit et Monitoring

### Consulter les Logs d'Emails
```python
from common.models import EmailLog

# Tous les emails non envoyés
emails_failed = EmailLog.objects.filter(statut='ECHEC')

# Emails d'OTP
otp_emails = EmailLog.objects.filter(type_email='OTP_LOGIN')

# Emails d'un patient spécifique
patient_emails = EmailLog.objects.filter(utilisateur=patient)

# Résumé du jour
from django.utils import timezone
today = timezone.now().date()
stats = EmailLog.objects.filter(date_creation__date=today).values('type_email', 'statut').count()
```

### Vue Admin
```python
# common/admin.py - Ajouter :
@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('type_email', 'destinataire', 'statut', 'date_envoi')
    list_filter = ('type_email', 'statut', 'date_creation')
    search_fields = ('destinataire', 'utilisateur__username')
    readonly_fields = ('uuid_message', 'date_creation', 'date_maj')
```

---

## 6. Performance & Async (Celery)

### ⚠️ Actuel : Envoi Synchrone
Les emails bloquent la requête API (~3-5 sec). Acceptable pour DEV, **problématique en PROD**.

### 🚀 Futur : Avec Celery
```python
# common/tasks.py
from celery import shared_task
from common.email_utils import send_notification

@shared_task
def async_send_notification(**kwargs):
    return send_notification(**kwargs)
```

```python
# common/email_utils.py
def send_notification(...):
    # ...
    try:
        # Envoi async
        async_send_notification.delay(to_email=to_email, ...)
    except:
        # Fallback sync
        send_notification(...)
```

---

## 7. Configuration SMS (Futur)

### Intégration Twilio (Exemple)
```python
# common/sms_utils.py
from twilio.rest import Client

SMS_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID')
SMS_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN')
SMS_FROM = env('TWILIO_PHONE')

client = Client(SMS_ACCOUNT_SID, SMS_AUTH_TOKEN)

def send_sms(phone: str, message: str):
    msg = client.messages.create(
        body=message,
        from_=SMS_FROM,
        to=phone
    )
    return msg.sid
```

---

## 8. Checklist Implémentation

- [x] Modèle `EmailLog` créé
- [x] `send_notification()` mise à jour avec logging
- [x] 4 nouvelles notifications ajoutées
- [x] Appels existants mis à jour
- [x] Migration appliquée
- [ ] Intégrer dans APIs (prescriptions, discharge, invoices)
- [ ] Admin EmailLog créé
- [ ] Tests unitaires pour notifications
- [ ] Configurer Celery (async)
- [ ] SMS integration (optionnel)
- [ ] Monitoring/Alertes sur ECHEC > 5%
- [ ] Rate limiting par utilisateur

---

## 9. Support & Troubleshooting

### Email non envoyé ?
```
Vérifier EmailLog.objects.filter(statut='ECHEC').first().erreur_message
```

### SMTP Connection Error ?
```env
# 1. Vérifier EMAIL_HOST / EMAIL_PORT
# 2. Si Gmail : Activer "Less secure app access" OU utiliser App Password
# 3. Test : python manage.py shell > send_notification(...)
```

### Trop lent ?
→ Configurer Celery + Redis

---

**Dernière mise à jour** : 2026-07-09  
**Version** : 1.0.0
