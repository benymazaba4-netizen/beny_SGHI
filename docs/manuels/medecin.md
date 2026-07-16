# Manuel Médecin SGHI

## Connexion
Rôle **MEDECIN** — ex. `medecin` / `Demo2026!`

## Parcours type
1. Consulter les **admissions actives**
2. Créer une **consultation** (code CIM-10 via recherche `/referentials/cim10`)
3. Prescrire une **ordonnance** et la **valider** (verrouillage + décrémentation stock)
4. Prescrire des **examens labo**
5. Gérer les **rendez-vous** et répondre aux **messages patients**

## Règles
- Patient hospitalisé : lier l'admission à la consultation
- Ordonnance validée : modification impossible
