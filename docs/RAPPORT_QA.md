# Rapport QA — SGHI ERP Médical v1.0

**Date :** 10 juillet 2026  
**Périmètre :** Backend API, portail web, mobile patient

## Résumé

| Domaine | Statut | Commentaire |
|---------|--------|-------------|
| Authentification JWT + MFA | ✅ Validé | Login, refresh, MFA TOTP, OTP e-mail |
| RBAC par rôle | ✅ Validé | Matrice permissions + isolation patient |
| Clinique & hospitalisation | ✅ Validé | Admissions, transferts, verrouillage optimiste |
| LIS laboratoire | ✅ Validé | Workflow complet + PDF signé |
| Pharmacie & facturation | ✅ Validé | Stocks FIFO, tiers-payant, journal comptable |
| Mobile patient | ✅ Validé | RDV, chat, PDF, observance |
| Paiement patient web/mobile | ✅ Validé | MTN/Airtel simulé, partiel, référence transaction |
| Échéancier paiements | ✅ Validé | Comptable → plan 2 échéances |
| Journal connexions | ✅ Validé | Admin → Sécurité |
| Calendrier RDV | ✅ Validé | Web RdvCalendar + mobile chips |
| Documents consultation | ✅ Validé | Upload PDF/imagerie post-consultation |
| Notifications | ✅ Validé | RDV + rappels médicamenteux |

## Tests automatisés exécutés

```bash
pytest -q
```

Couverture principale :
- Auth (login, credentials invalides)
- Chiffrement AES-256 champs sensibles
- Accès patient (scope dossier)
- Rendez-vous et rappels e-mail
- Intégration admission / prescription immuable / LIS
- Gouvernance (archivage, anonymisation)
- Rappels médicamenteux (idempotence)

**Total :** ~27 tests backend

## Tests manuels (UAT)

| Scénario | Résultat |
|----------|----------|
| Parcours démo 15 min (`DEMO.md`) | ✅ |
| Téléchargement PDF labo/facture patient | ✅ |
| Dashboard admin KPIs Redis | ✅ |
| UI gouvernance admin | ✅ |
| Plan de soins médecin + mobile | ✅ |
| Calendrier gardes RH | ✅ |

## Points connus / hors périmètre v1

- Stack ELK/Grafana : métriques Prometheus uniquement
- FHIR : endpoints simplifiés Patient/Observation
- Tests E2E frontend : non automatisés (build Vue validé en CI)
- Tests de charge : non exécutés (pagination + indexation en place)

## Conclusion

Le système est **prêt pour démonstration et rendu** au regard du cahier des charges v1.0. Les flux métier critiques sont fonctionnels et testés.
