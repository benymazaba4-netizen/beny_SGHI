# Dossier d'Architecture Technique (DAT) — SGHI ERP Médical v1.0

## 1. Vue d'ensemble

Le SGHI est un ERP hospitalier full-stack (Web + Mobile) couvrant le parcours patient complet.

## 2. Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3.12, Django 6, Django Ninja |
| Frontend | Vue.js 3, Tailwind CSS, Pinia, Axios |
| Mobile | Flutter (iOS/Android) |
| BDD | PostgreSQL (prod), SQLite (dev) |
| Cache | Redis |
| Auth | JWT + refresh tokens, MFA TOTP |
| Email | SMTP Gmail |
| Monitoring | `/api/v1/sante`, `/api/v1/metrics` (Prometheus) |

## 3. Architecture logique

```
Clients (Vue / Flutter)
        ↓ HTTPS
API REST /api/v1/ (Django Ninja)
        ↓
Services métier (clinical, laboratory, billing, …)
        ↓
PostgreSQL + Redis + Media chiffré
```

## 4. Modules applicatifs

- **authentication** : JWT, MFA, refresh tokens
- **clinical** : patients, admissions, consultations, constantes, plans de soins
- **hospital_structure** : bâtiments, services, chambres, lits
- **prescriptions** : e-ordonnances verrouillées, administrations
- **laboratory** : LIS complet (commande → PDF signé)
- **pharmacy** : stocks, lots, alertes
- **billing** : facturation, tiers-payant, journal comptable
- **rh** : personnel, gardes, congés, paie
- **appointments** : rendez-vous, disponibilités médecins
- **messaging** : chat médecin-patient
- **notifications** : in-app + push FCM
- **referentials** : CIM-10
- **governance** : archivage, anonymisation, journal accès
- **interop** : endpoints FHIR R4 simplifiés
- **audit** : journal immuable SHA256

## 5. Sécurité

- RBAC par rôle + matrice permissions (`common/permissions.py`)
- Chiffrement Fernet AES-256 (NIN, SS)
- Rate limiting 100 req/min/IP
- Audit trail sur actions sensibles
- Scan antivirus ClamAV (optionnel)
- CSRF, CORS, HSTS en production

## 6. Déploiement

- Docker Compose : Postgres + Redis + backend + frontend
- CI : GitHub Actions (pytest + build)
- CD : workflow `cd.yml` (staging)
- Backup : `scripts/backup.ps1`

## 7. Interopérabilité

- FHIR R4 : `/api/v1/fhir/Patient`, `/api/v1/fhir/Observation`
- Politique dépréciation API v1 : 6 mois (`API_DEPRECATION_POLICY`)
