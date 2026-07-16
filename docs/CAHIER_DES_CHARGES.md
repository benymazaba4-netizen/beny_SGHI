# Cahier des charges — SGHI / SGHL ERP Médical v1.0

**Projet :** ERP Médical Intégré (Web + Mobile)  
**Superviseur :** Prof. MVIBUNDULU Gaetan  
**Version :** 1.0 — Mars 2026

## 1. Vision

Digitaliser le parcours patient (admission → suivi post-hospitalisation) avec traçabilité immuable, sécurité bancaire, haute disponibilité et gouvernance des données.

## 2. Stack

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3.12, Django 6, Django Ninja |
| Web | Vue.js 3, Tailwind, Pinia |
| Mobile | Flutter (PWA, Android, iOS) |
| BDD | PostgreSQL / SQLite |
| Cache | Redis |
| Auth | JWT, MFA TOTP, AES-256 |

## 3. Modules fonctionnels

- **Clinique** : CIM-10, prescriptions verrouillées, admissions/transferts, plans de soins, documents consultation
- **LIS** : workflow complet, validation biologiste, PDF signé
- **Pharmacie** : stocks FIFO, alertes
- **Facturation** : moteur auto, tiers-payant, paiements partiels/échelonnés, journal comptable
- **RH** : gardes (calendrier), congés, présences
- **Mobile patient** : RDV, chat, observance, paiement en ligne (simulé)
- **Gouvernance** : archivage, anonymisation, journal accès
- **Sécurité** : audit SHA256, journal connexions, MFA

## 4. Règles métier critiques

- 1 lit = 1 patient
- Prescription verrouillée = immuable
- Résultat labo validé = immuable
- Journal comptable immuable
- Isolation stricte des données patientes

## 5. Livrables

- Code source (backend, web, mobile)
- DAT, MCD, API, manuels, rapport QA
- APK mobile (`scripts/build-mobile.ps1`)
- Checklist de rendu (`docs/RENDU_CHECKLIST.md`)

## 6. État d'implémentation v1.0

| Exigence | Statut |
|----------|--------|
| Parcours clinique complet | ✅ |
| LIS + PDF | ✅ |
| Facturation + paiements | ✅ (simulation Mobile Money) |
| Mobile observance | ✅ |
| Gouvernance UI | ✅ |
| FHIR simplifié | ✅ partiel |
| ELK / Grafana | ⏳ hors MVP |
| Passerelle paiement réelle | ⏳ simulation |

Voir `docs/RAPPORT_QA.md` pour la validation détaillée.
