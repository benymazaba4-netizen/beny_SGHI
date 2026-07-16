# Checklist de rendu — SGHI ERP Médical

**Date limite :** demain  
**Superviseur :** Prof. MVIBUNDULU Gaetan

## Livrables documentaires

- [x] Dossier d'Architecture Technique (`docs/DAT.md`)
- [x] Modèle Conceptuel de Données (`docs/MCD.md`)
- [x] Dictionnaire API (`docs/API.md`)
- [x] Manuels utilisateur (`docs/manuels/`)
- [x] Guide démo (`DEMO.md`)
- [x] Rapport QA (`docs/RAPPORT_QA.md`)
- [x] Checklist de rendu (ce document)

## Livrables techniques

- [x] Code source backend Django + API REST v1
- [x] Portail web Vue 3 (dashboards par rôle)
- [x] Application mobile Flutter patient (PWA + Android)
- [x] Scripts déploiement (`scripts/`, `docker-compose.yml`)
- [x] CI/CD GitHub Actions (`.github/workflows/`)
- [x] Cahier des charges formel (`docs/CAHIER_DES_CHARGES.md`)
- [x] Paiement patient web + mobile (MTN/Airtel simulé)
- [x] Échéancier paiements (comptable)
- [x] Journal connexions (admin)
- [x] Calendrier RDV (web + mobile)
- [x] Upload documents consultation (médecin)
- [ ] APK release généré (`scripts/build-mobile.ps1`)
- [ ] Lien hébergé staging (à renseigner)

## Démonstration recommandée (15 min)

1. **Secrétaire** — admission patient
2. **Médecin** — consultation CIM-10, prescription, plan de soins, demande labo
3. **Infirmier** — constantes vitales, administration, alertes doses
4. **Biologiste** — validation NFS + PDF
5. **Pharmacien** — stocks et alertes
6. **Comptable** — facture auto, tiers-payant, paiement partiel
7. **Patient** — mobile : dossier, PDF, RDV, observance
8. **Admin** — KPIs, gouvernance, audit, MFA

## Commandes de démarrage

```powershell
.\scripts\start-all.ps1
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
cd frontend-web; npm run dev
cd mobile-patient; flutter run -d chrome --web-port=5180
```

**Compte démo :** `admin` / `patient` / `medecin` — mot de passe `Demo2026!`

## Tests avant rendu

```powershell
.\venv\Scripts\python.exe -m pytest -q
cd frontend-web; npm run build
cd mobile-patient; flutter test
```
