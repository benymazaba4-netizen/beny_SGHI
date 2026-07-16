#!/usr/bin/env bash
# Build Render — API Django
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
