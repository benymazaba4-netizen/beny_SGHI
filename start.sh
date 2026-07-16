#!/usr/bin/env bash
# Démarrage Render — migrations puis Gunicorn
set -o errexit

python manage.py migrate --noinput

# Seed optionnel (démo) — activer via SEED_DEMO=True sur Render
if [ "${SEED_DEMO:-False}" = "True" ] || [ "${SEED_DEMO:-False}" = "true" ]; then
  python manage.py seed_demo_users || true
fi

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
