# Manuel Administrateur SGHI

## Connexion
- URL : `/login` — rôle **ADMIN**
- Identifiant démo : `admin` / `Demo2026!`

## Fonctions
1. **Dashboard KPIs** — taux d'occupation, recettes, examens en attente
2. **Structure hospitalière** — bâtiments, services, lits
3. **RH** — personnel, planning gardes (création via API POST `/rh/planning-gardes`)
4. **Audit** — journal immuable des actions
5. **Gouvernance** — onglet Admin → archivage dossiers, jobs d'anonymisation, journal accès
6. **MFA** — activation TOTP pour les comptes sensibles

## Supervision
- Santé : `/api/v1/sante`
- Métriques : `/api/v1/metrics`
