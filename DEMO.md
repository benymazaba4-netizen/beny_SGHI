# SGHI — Guide démo pas à pas

**Mot de passe commun :** `Demo2026!`  
**OTP connexion :** code envoyé à `benymazaba4@gmail.com` (tous les comptes démo)

## Préparation (1 commande)

```powershell
.\scripts\prepare-demo.ps1

# Puis dans 3 terminaux :
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
cd frontend-web; npm run dev
cd mobile-patient; flutter run -d chrome --web-port=5180
```

| Service | URL |
|---------|-----|
| API + docs | http://127.0.0.1:8000/api/v1/docs |
| Portail web | http://localhost:5173 |
| Mobile PWA | http://localhost:5180 |

---

## Parcours démo (~15 min)

### 1. Secrétaire → Admission
**Login :** `secretaire`  
**Route :** `/dashboard/secretaire`

1. Connexion → saisir le code OTP reçu par e-mail
2. Onglet **Admissions** → voir l'admission active de **Joseph Kabongo** (Médecine interne)
3. *(Optionnel live)* Onglet **+ Admission** → créer une nouvelle admission sur un lit libre
4. Onglet **RDV** → voir le rendez-vous de contrôle planifié

---

### 2. Médecin → Consultation + prescription + labo
**Login :** `medecin`  
**Route :** `/dashboard/medecin`

1. Onglet **Patients** / **Hospitalisations** → patient `patient` hospitalisé
2. Onglet **Actions médicales** :
   - **Nouvelle consultation** : motif + diagnostic CIM-10 (chercher `A09`)
   - **Prescription** : Paracétamol 500mg, 3x/jour, 7 jours → Valider
   - **Demande labo** : NFS (ou autre examen)
3. Onglet **Laboratoire** → voir les demandes en cours

> Le seed pré-crée déjà une consultation A09 + prescription + NFS. Vous pouvez **montrer l'existant** ou **refaire en live**.

---

### 3. Infirmier → Constantes vitales
**Login :** `infirmier`  
**Route :** `/dashboard/infirmier`

1. Onglet **Constantes** → graphiques avec historique (3 mesures seed)
2. Onglet **Soins** → saisir **nouvelles constantes** sur l'admission active :
   - TA, FC, température, SpO2
3. *(Optionnel)* Enregistrer une **administration** de médicament (prescription Paracétamol)

---

### 4. Biologiste → Validation NFS + PDF
**Login :** `biologiste`  
**Route :** `/dashboard/biologiste`

1. Onglet **Validation** → NFS de Joseph Kabongo en attente
2. Cliquer **Valider** → PDF généré et publié au patient
3. Le CRP est déjà validé (visible patient immédiatement)

> Action clé en live : la validation NFS.

---

### 5. Pharmacien → Stocks
**Login :** `pharmacien`  
**Route :** `/dashboard/pharmacien`

1. Onglet **Stocks** → Paracétamol, Amoxicilline, Sérum physiologique (500 unités chacun)
2. *(Optionnel)* Onglet **Réception/Mouvements** → ajouter un lot ou mouvement

---

### 6. Comptable → Facture + paiement partiel
**Login :** `comptable`  
**Route :** `/dashboard/comptable`

1. Onglet **Factures** → facture impayée ~50 000 FCFA (PDF disponible)
2. Onglet **Facturation** → enregistrer un **paiement partiel** (ex. 20 000 FCFA)
3. Vérifier statut **PARTIELLE** et solde restant
4. Onglet **Journal** → écriture comptable

> Action clé en live : le paiement partiel.

---

### 7. Patient → Mobile (dossier, RDV, paiement)
**Login :** `patient`  
**Mobile :** http://localhost:5180 ou app Flutter

1. Connexion OTP → accueil patient
2. **Santé** → consultation A09, ordonnance Paracétamol, résultats labo (CRP + NFS après étape 4)
3. **RDV** → rendez-vous de contrôle planifié (J+3)
4. **Profil / Factures** → télécharger PDF facture + payer le solde (MTN/Airtel simulé)
5. **Paiement** → régler le reste (ex. 30 000 FCFA)

> Web patient : http://localhost:5173 (portail `/` une fois connecté)

---

### 8. Admin → KPIs, utilisateurs, gouvernance
**Login :** `admin` ou `superadmin`  
**Route :** `/dashboard/admin`

| Compte | Niveau |
|--------|--------|
| `admin` | Gestion courante (ne modifie pas le super-admin) |
| `superadmin` | Droits complets sur tous les comptes |

1. **Vue d'ensemble** → KPIs (occupation, recettes, examens en attente)
2. **Utilisateurs** → modifier un compte (ex. téléphone médecin)
3. **Structure** → bâtiments, services, lits
4. **RH & Gardes** → personnel + planning
5. **Gouvernance** → archiver dossier, job anonymisation
6. **Sécurité** → activer MFA TOTP (optionnel)
7. **Audit** → journal des actions

---

## Données seed (résumé)

| Élément | État après `seed_demo_users` |
|---------|------------------------------|
| Patient hospitalisé | Joseph Kabongo, MED-INT |
| Consultation | A09 — syndrome infectieux |
| Prescription | Paracétamol 500mg × 7 jours |
| NFS | En attente validation (biologiste) |
| CRP | Validé + PDF patient |
| Constantes | 3 mesures (graphiques infirmier) |
| Plan de soins | Surveillance post-fébrile |
| Stocks pharmacie | 3 médicaments, 500 unités |
| Facture | 50 000 FCFA impayée + PDF |
| RDV | Contrôle J+3 confirmé |
| Personnel RH | 8 rôles dont comptable |

## Réinitialiser la démo

```powershell
.\scripts\prepare-demo.ps1
```

Rejoue le seed : remet NFS en validation, facture impayée avec PDF, RDV, etc.

## Tests

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

## Comptes

| Login | Rôle |
|-------|------|
| `secretaire` | Secrétaire |
| `medecin` | Médecin |
| `infirmier` | Infirmier |
| `biologiste` | Biologiste |
| `pharmacien` | Pharmacien |
| `comptable` | Comptable |
| `patient` | Patient |
| `admin` | Administrateur |
| `superadmin` | Super-administrateur |
