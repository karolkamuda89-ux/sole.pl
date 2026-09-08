"""
Komenda: python manage.py ensure_superuser

Po co: Render (darmowy plan) nie daje dostępu do terminala (shell) na
serwerze, więc zwykłe interaktywne `createsuperuser` (ani `changepassword`)
tam nie zadziała. Ta komenda robi to samo, ale bezobsługowo — czyta dane
z trzech zmiennych środowiskowych i tworzy konto TYLKO jeśli jeszcze nie
istnieje. Dzięki temu jest bezpieczna do uruchamiania przy KAŻDYM wdrożeniu
(patrz start.sh) — nie wywali błędu i nie nadpisze hasła przy kolejnych
deployach.

Wymagane zmienne środowiskowe (ustawiane w panelu Render, NIE w kodzie):
    DJANGO_SUPERUSER_USERNAME
    DJANGO_SUPERUSER_EMAIL
    DJANGO_SUPERUSER_PASSWORD

Jeśli którejś brakuje, komenda po prostu nic nie robi (i informuje o tym) —
przydatne np. lokalnie, gdzie i tak masz już konto z `createsuperuser`.

Zapomniane hasło do panelu admina — jak zresetować (bez shella):
    1. W Render → Environment → ustaw DJANGO_SUPERUSER_PASSWORD na nowe hasło.
    2. Tam samo dodaj DJANGO_SUPERUSER_FORCE_RESET=True.
    3. Save, rebuild, and deploy — przy starcie konto dostanie nowe hasło,
       nawet jeśli już istniało.
    4. Zaloguj się nowym hasłem, POTEM usuń zmienną DJANGO_SUPERUSER_FORCE_RESET
       (albo ustaw na cokolwiek innego niż "True") — inaczej hasło będzie się
       resetować do tej samej wartości przy każdym kolejnym deployu, co
       nadpisałoby np. zmianę hasła zrobioną wprost w panelu /admin/.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Tworzy superusera z danych w zmiennych środowiskowych, jeśli jeszcze nie istnieje."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        force_reset = os.environ.get("DJANGO_SUPERUSER_FORCE_RESET", "False") == "True"

        if not (username and email and password):
            self.stdout.write(
                "Pomijam — brak DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD w środowisku."
            )
            return

        User = get_user_model()
        user = User.objects.filter(username=username).first()

        if user:
            if force_reset:
                user.set_password(password)
                user.save(update_fields=["password"])
                self.stdout.write(self.style.SUCCESS(
                    f"Zresetowano hasło superusera '{username}' "
                    "(DJANGO_SUPERUSER_FORCE_RESET=True)."
                ))
            else:
                self.stdout.write(f"Superuser '{username}' już istnieje — pomijam.")
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Utworzono superusera '{username}'."))
