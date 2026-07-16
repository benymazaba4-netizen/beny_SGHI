# Dictionnaire API REST v1 — SGHI

Base URL : `/api/v1/`

Documentation interactive : `/api/v1/docs`

## Authentification

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/auth/login` | Connexion JWT |
| POST | `/auth/login/mfa` | Connexion avec TOTP |
| POST | `/auth/refresh` | Rotation refresh token |
| POST | `/auth/register` | Inscription patient |

Header : `Authorization: Bearer <token>`

## Modules principaux

| Préfixe | Module |
|---------|--------|
| `/clinical/` | Patients, admissions, consultations, constantes, plans de soins |
| `/prescriptions/` | Ordonnances, administrations |
| `/laboratory/` | LIS complet |
| `/pharmacy/` | Stocks |
| `/billing/` | Facturation, paiements |
| `/rh/` | Personnel, gardes, congés |
| `/appointments/` | Rendez-vous, disponibilités |
| `/messaging/` | Chat |
| `/notifications/` | Notifications, devices FCM |
| `/referentials/` | CIM-10 |
| `/governance/` | Archivage, anonymisation |
| `/fhir/` | Interopérabilité FHIR R4 |
| `/dashboard/` | KPIs (cache Redis) |
| `/audit/` | Journal d'audit |
| `/sante`, `/metrics` | Supervision |

## Codes HTTP

- `200` OK — `201` Créé — `400` Erreur métier — `401` Non authentifié — `403` Accès refusé — `404` Introuvable — `409` Conflit version

## Versioning

Version actuelle : **1.0.0**. Politique de dépréciation : 6 mois avant retrait d'un endpoint.
