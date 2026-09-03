#!/usr/bin/env bash
# Skrypt startowy na Render — uruchamia się przy KAŻDYM starcie kontenera
# (czyli po każdym deployu, i po każdym "wybudzeniu" usługi ze snu na
# darmowym planie), tuż PRZED odpaleniem gunicorna.
#
# Dlaczego to nie jest w build.sh: build.sh działa w kroku budowania, a
# gunicorn startuje w kroku uruchamiania — na Render to, co build.sh zapisze
# na dysk (np. media/ z prawdziwymi zdjęciami apartamentów), nie musi
# przetrwać do momentu, gdy faktycznie odpowiada na żądania (potwierdzone:
# `import_apartments` w build.sh raportował sukces przy KAŻDYM deployu, a
# mimo to zdjęcia i tak dawały 404 na żywej stronie). collectstatic działa
# w build.sh bez problemu (whitenoise/Render obsługuje to jako standardowy
# przypadek), więc to zostaje tam bez zmian — tylko krok, który zapisuje
# PRAWDZIWE pliki mediów, przenosi się tutaj, żeby na pewno działał w TYM
# SAMYM kontenerze, który potem serwuje żądania.
#
# Wszystkie poniższe komendy są bezpieczne do uruchamiania wielokrotnie
# (patrz komentarze w każdej z nich) — nie szkodzi, że lecą przy każdym
# starcie, nawet gdy nic się nie zmieniło.
set -o errexit

python manage.py migrate
python manage.py ensure_superuser
python manage.py import_apartments
python manage.py refresh_alt_text

exec gunicorn config.wsgi:application
