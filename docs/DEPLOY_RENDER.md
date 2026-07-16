# Déploiement Render — SGHI ERP Médical

## Architecture

| Service | Type Render | Rôle |
|---------|-------------|------|
| `sghi-db` | PostgreSQL (free) | Base de données |
| `sghi-api` | Web Service Python | API Django + Gunicorn |
| `sghi-patient` | Static Site | Flutter Web (portail patient) |

Fichier Blueprint : `render.yaml` à la racine du dépôt.

---

## Prérequis

1. Compte [Render](https://dashboard.render.com)
2. Dépôt GitHub/GitLab poussé avec ces fichiers
3. Branche `main` (ou adapter `branch` dans `render.yaml`)

---

## Déploiement rapide (Blueprint)

1. Dashboard Render → **New** → **Blueprint**
2. Connecter le dépôt `SGHI_ERP_Medical`
3. Render lit `render.yaml` et crée DB + API (+ static Flutter)
4. Cliquer **Apply**

Attendre 5–10 min pour l’API. L’URL ressemblera à :

`https://sghi-api.onrender.com`

Docs API : `https://sghi-api.onrender.com/api/v1/docs`

---

## Variables d’environnement importantes

Déjà prévues dans `render.yaml`. À ajuster après coup :

| Variable | Valeur |
|----------|--------|
| `CORS_ALLOWED_ORIGINS` | URL exacte du Flutter web, ex. `https://sghi-patient.onrender.com` |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | Gmail App Password (OTP réel) |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` en prod mail |
| `SEED_DEMO` | `True` au 1er lancement, puis `False` |
| `OTP_DEV_BYPASS_CODE` | Laisser pour démo ; retirer en prod réelle |

Compte démo (si `SEED_DEMO=True`) : `patient` / `Demo2026!`

---

## Flutter Web → pointer vers l’API Render

### Option A — Build local (recommandé ce soir, plus rapide)

```powershell
cd mobile-patient
flutter pub get
flutter build web --release --dart-define=API_BASE_URL=https://sghi-api.onrender.com/api/v1
```

Puis sur Render : **New → Static Site**

- Root Directory : `mobile-patient`
- Build Command : `echo "prebuilt"` (ou laisser vide si tu commits `build/web`)
- Publish Directory : `build/web`

Ou uploader le dossier `build/web` via un Static Site qui clone le repo après commit de `build/web`.

### Option B — Build sur Render

Le service `sghi-patient` dans `render.yaml` clone Flutter et build.
Remplace `https://sghi-api.onrender.com` dans `buildCommand` par **ton** URL API réelle si le nom de service diffère.

Puis mets à jour `CORS_ALLOWED_ORIGINS` sur `sghi-api` avec l’URL du static site.

---

## Déploiement manuel (sans Blueprint)

### 1. PostgreSQL

New → PostgreSQL → Free → créer `sghi-db`

### 2. Web Service API

New → Web Service → repo → Runtime **Python 3**

- Build : `chmod +x build.sh start.sh && ./build.sh`
- Start : `./start.sh`
- Health check : `/api/v1/docs`

Env vars (copier depuis Internal Database URL) :

```
DEBUG=False
SECRET_KEY=<générer>
DATABASE_URL=<Internal Database URL Render>
ALLOWED_HOSTS=.onrender.com
CORS_ALLOWED_ORIGINS=https://ton-front.onrender.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SEED_DEMO=True
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

---

## Vérifications post-déploiement

1. Ouvrir `https://sghi-api.onrender.com/api/v1/docs` → OK
2. Flutter web charge sans erreur CORS
3. Login `patient` / `Demo2026!` (si seed activé)
4. Sur free tier, l’API s’endort après ~15 min d’inactivité (cold start ~30–60 s)

---

## Notes free tier

- PostgreSQL free expire après 30 jours (plan Render)
- Sleep après inactivité
- Pas de Redis : le cache fichier Django fonctionne (OTP OK)
- Médias uploadés sont éphémères (disque non persistant) — OK pour démo
