# SGHI — Documentation technique

## Contenu

| Document | Description |
|----------|-------------|
| [DAT.md](DAT.md) | Dossier d'Architecture Technique |
| [MCD.md](MCD.md) | Modèle Conceptuel de Données |
| [API.md](API.md) | Dictionnaire API REST v1 |
| [manuels/](manuels/) | Manuels utilisateur par rôle |
| [RENDU_CHECKLIST.md](RENDU_CHECKLIST.md) | Checklist livrables et démo |
| [RAPPORT_QA.md](RAPPORT_QA.md) | Rapport qualité / tests |
| [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md) | Spécifications fonctionnelles v1.0 |

## Démarrage

```powershell
.\scripts\start-demo.ps1
python manage.py load_cim10
```

## Supervision

- Santé : `GET /api/v1/sante`
- Métriques Prometheus : `GET /api/v1/metrics`
- OpenAPI : `/api/v1/docs`

Supervisé par Prof. MVIBUNDULU Gaetan — Mars 2026
