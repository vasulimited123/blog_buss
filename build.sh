#!/usr/bin/env bash
# Render build script — runs on every deploy.
# Installs dependencies, collects static files, and applies migrations.
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate
