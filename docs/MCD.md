# Modèle Conceptuel de Données (MCD) — SGHI

## Entités principales

### Patient & clinique
- **Patient** 1—1 **Utilisateur** (rôle PATIENT)
- **Patient** 1—N **Admission** — N—1 **ServiceHospitalier**, **Lit**
- **Patient** 1—N **Consultation** — diagnostic CIM-10
- **Patient** 1—N **ConstanteVitale**
- **Patient** 1—N **PlanSoin**

### Prescriptions & pharmacie
- **Prescription** 1—N **LignePrescription** — N—1 **Medicament**
- **LignePrescription** 1—N **AdministrationMedicament**
- **LotMedicament** — stock, péremption, **MouvementStock**

### Laboratoire (LIS)
- **DemandeExamen** → **Prelevement** → **ResultatExamen** (immuabilité post-validation)

### Facturation
- **Facture** 1—N **LigneFacture**
- **PriseEnChargeAssurance** — tiers-payant
- **TransactionPaiement** — journal **JournalComptable** (chaîne hash)

### Rendez-vous & communication
- **DisponibiliteMedecin** — créneaux
- **RendezVous** — patient, médecin, service
- **Conversation** 1—N **Message**
- **Notification**, **DeviceToken** (FCM)

### RH
- **Personnel** 1—1 **Utilisateur**
- **PlanningGarde**, **Presence**, **Conge**, **FichePaie**

### Gouvernance
- **JournalAccesDossier** — traçabilité lectures dossier
- **ArchiveRecord** — politique rétention 20 ans
- **AnonymizationJob** — export statistique anonymisé

### Référentiels
- **CodeCIM10** — code, libellé, chapitre

### Audit
- **AuditLog** — chaîne SHA256 immuable (user, IP, old/new value)

## Contraintes métier clés

1. **1 lit = 1 patient** (admission active unique)
2. **Prescription validée = immuable**
3. **Résultat labo validé = immuable**
4. **Patient PATIENT** : accès restreint à son `patient_id`
