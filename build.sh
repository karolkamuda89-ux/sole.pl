#!/usr/bin/env bash
# Skrypt budowania na Render — uruchamia się automatycznie przy każdym
# `git push` (patrz Start/Build Command w panelu Render). Zostaje tu TYLKO
# instalacja zależności i collectstatic — to jedyne dwa kroki, które
# faktycznie muszą przetrwać z kroku budowania do kroku uruchamiania
# (a collectstatic, w odróżnieniu od zapisu prawdziwych zdjęć do media/,
# potwierdzone działa poprawnie w tym miejscu). Migracje bazy, tworzenie
# superusera i dogrywanie zdjęć ofert przeniesione do start.sh — patrz
# komentarz tam, dlaczego.
set -o errexit  # przerwij cały build, jeśli którykolwiek krok się nie powiedzie

pip install -r requirements.txt

# --ignore=raw pomija core/static/core/img/raw/ (surowiec, i tak nie ma go
# w repo — patrz .gitignore) — zostawione na wypadek gdyby ktoś kiedyś
# uruchomił to bez świeżego clone. --ignore="*.mp4" pomija nagrania wideo
# apartamentów (nie są to pliki do serwowania jako statyczne assety).
python manage.py collectstatic --noinput --ignore=raw --ignore="*.mp4"
