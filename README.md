# SGHI — Système de Gestion Hospitalière et de Laboratoire

ERP médical full-stack : backend Django Ninja, portail web Vue 3, application mobile Flutter patient (PWA + Android/iOS).

## Base de données PostgreSQL

```powershell
# Option 1 — Docker (recommandé)
.\scripts\setup-postgres.ps1

# Option 2 — PostgreSQL installé localement (Windows)
# Créer la base sghi_db, puis :
.\scripts\setup-postgres.ps1 -SkipDocker
```

Variables `.env` (valeurs Docker par défaut) :

```env
DB_ENGINE=postgresql
DB_NAME=sghi_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

Conteneur seul : `docker compose up -d db` — backup : `.\scripts\backup.ps1`

## Démarrage rapide (Windows)

```powershell
.\scripts\start-all.ps1

# Terminal 1 — API
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

# Terminal 2 — Portail web
cd frontend-web; npm install; npm run dev

# Terminal 3 — Mobile PWA
cd mobile-patient; flutter pub get; flutter run -d chrome --web-port=5180
```

| Service | URL |
|---------|-----|
| API + docs | http://127.0.0.1:8000/api/v1/docs |
| Portail web | http://localhost:5173 |
| Mobile PWA | http://localhost:5180 |
| Mailpit (e-mails) | http://127.0.0.1:8025 |

**Comptes démo** (mot de passe : `Demo2026!`) :

| Compte | Rôle | Niveau |
|--------|------|--------|
| `patient` | Patient | — |
| `admin` | Administrateur | Gestion courante (utilisateurs sauf super-admin) |
| `superadmin` | Administrateur | Super-administrateur (droits complets) |
| `medecin` / `secretaire` | Personnel | — |

Pour un super-admin hors démo : `python manage.py create_superadmin`

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend | Python 3.12, Django 6, Django Ninja |
| Frontend Web | Vue.js 3, Tailwind CSS, Pinia |
| Mobile | Flutter (Web PWA, Android, iOS) |
| Base de données | PostgreSQL (prod) / SQLite (dev) |
| Cache | Redis (KPIs dashboard) |
| Auth | JWT + refresh tokens, MFA TOTP |
| Notifications | In-app + push FCM + e-mails HTML SMTP |
| Monitoring | `/api/v1/sante`, `/api/v1/metrics` (Prometheus) |
| Interop | FHIR R4 (`/api/v1/fhir/`) |

## Modules fonctionnels

Clinical, Hospital, Laboratory, Pharmacy, Billing, RH, Appointments, Messaging, Notifications, Prescriptions, Auth/MFA, Audit, Dashboard, Governance, Referentials (CIM-10), FHIR.

## E-mails (SMTP + HTML)

```powershell
.\scripts\start-mailpit.ps1
python manage.py test_email --to patient@example.com
python manage.py send_rdv_reminders
.\scripts\schedule-rdv-reminders.ps1   # planification Windows
```

E-mails automatiques HTML : inscription, confirmation RDV, rappel RDV (24 h), résultat labo.

## Push mobile (FCM)

```powershell
.\scripts\setup-firebase.ps1
python manage.py send_test_push --username patient
```

Configurer `FCM_SERVER_KEY` dans `.env`. Voir `mobile-patient/README.md`.

## Build mobile

```powershell
.\scripts\build-mobile.ps1
```

## Tests

```bash
pytest
```

16 tests (auth, RDV, rappels e-mail, intégration, chiffrement…).

## Production

```env
DB_ENGINE=postgresql
REDIS_URL=redis://127.0.0.1:6379/1
SECURE_SSL_REDIRECT=True
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
FCM_SERVER_KEY=votre_cle_fcm
```

Docker : `docker compose up --build`

## Documentation

Dossier **[docs/](docs/)** : DAT, MCD, API, checklist de rendu, rapport QA.

| Document | Description |
|----------|-------------|
| [RENDU_CHECKLIST.md](docs/RENDU_CHECKLIST.md) | Checklist livrables et démo |
| [RAPPORT_QA.md](docs/RAPPORT_QA.md) | Rapport qualité / tests |

## Supervision

Prof. MVIBUNDULU Gaetan — Mars 2026
