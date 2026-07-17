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
| `EMAIL_HOST_USER` | Compte Gmail expéditeur (ex. `benymazaba4@gmail.com`) |
| `EMAIL_HOST_PASSWORD` | Mot de passe d’application Gmail (16 caractères) — **secret Render** |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_USE_REAL_SMTP` | `True` |
| `SEED_DEMO` | `True` au 1er lancement, puis `False` |
| `OTP_DEV_BYPASS_CODE` | Inutile si `DEBUG=False` ; retirer en prod réelle |

### OTP e-mail qui échoue sur Render (cause réelle)

**Render Free bloque les ports SMTP `25`, `465` et `587`.**  
Gmail SMTP ne peut donc **pas** fonctionner, même avec un mot de passe d’application correct.

#### Option A — Démo immédiate (bypass OTP)

Sur **`sghi-api`** → Environment :

```
OTP_ALLOW_BYPASS=True
OTP_DEV_BYPASS_CODE=123456
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Puis à la connexion, saisir le code **`123456`**.

#### Option B — Vrais e-mails sur Free (Brevo HTTPS) — **recommandé**

1. Créer un compte gratuit [Brevo](https://app.brevo.com)
2. **SMTP & API** → **API keys** → Create a new API key (copier la clé `xkeysib-…`)
3. **Senders** → Add a sender → `benymazaba4@gmail.com` → valider le lien reçu par e-mail
4. Sur Render → **`sghi-api`** → Environment :

```
BREVO_API_KEY=xkeysib-xxxxxxxx
BREVO_SENDER_EMAIL=benymazaba4@gmail.com
BREVO_SENDER_NAME=SGHI ERP
OTP_ALLOW_BYPASS=False
```

5. **Save** → redéploiement / redémarrage
6. Tester la connexion : l’OTP arrive dans la boîte du compte utilisateur

En local (optionnel) : ajouter les mêmes variables dans `.env`, puis :

```
python manage.py check_email
python manage.py test_email --to benymazaba4@gmail.com
```

#### Option C — Plan payant Render

Un instance type payant débloque SMTP → Gmail classique possible.

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
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<gmail>
EMAIL_HOST_PASSWORD=<app password>
EMAIL_USE_REAL_SMTP=True
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
