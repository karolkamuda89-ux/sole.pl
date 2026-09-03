#!/usr/bin/env bash
# Skrypt budowania na Render — uruchamia się automatycznie przy każdym
# `git push` (patrz render.yaml, buildCommand). Wszystkie kroki są
# bezpieczne do uruchomienia wielokrotnie (idempotentne):
#   - collectstatic: zawsze nadpisuje tym samym wynikiem
#   - migrate: pomija migracje już zastosowane
#   - ensure_superuser: pomija, jeśli konto już istnieje
#   - import_apartments: pomija ofertę, jeśli już istnieje (patrz --force w kodzie)
#   - refresh_alt_text: zawsze ustawia ten sam, przewidywalny tekst
set -o errexit  # przerwij cały build, jeśli którykolwiek krok się nie powiedzie

pip install -r requirements.txt

# --ignore=raw pomija core/static/core/img/raw/ (surowiec, i tak nie ma go
# w repo — patrz .gitignore) — zostawione na wypadek gdyby ktoś kiedyś
# uruchomił to bez świeżego clone. --ignore="*.mp4" pomija nagrania wideo
# apartamentów (nie są to pliki do serwowania jako statyczne assety).
python manage.py collectstatic --noinput --ignore=raw --ignore="*.mp4"

python manage.py migrate
python manage.py ensure_superuser
python manage.py import_apartments
python manage.py refresh_alt_text
