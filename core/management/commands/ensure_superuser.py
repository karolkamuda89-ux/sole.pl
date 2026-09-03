"""
Komenda: python manage.py ensure_superuser

Po co: Render (darmowy plan) nie daje dostępu do terminala (shell) na
serwerze, więc zwykłe interaktywne `createsuperuser` tam nie zadziała.
Ta komenda robi to samo, ale bezobsługowo — czyta dane z trzech zmiennych
środowiskowych i tworzy konto TYLKO jeśli jeszcze nie istnieje. Dzięki
temu jest bezpieczna do uruchamiania przy KAŻDYM wdrożeniu (patrz
build.sh) — nie wywali błędu i nie nadpisze hasła przy kolejnych deployach.

Wymagane zmienne środowiskowe (ustawiane w panelu Render, NIE w kodzie):
    DJANGO_SUPERUSER_USERNAME
    DJANGO_SUPERUSER_EMAIL
    DJANGO_SUPERUSER_PASSWORD

Jeśli którejś brakuje, komenda po prostu nic nie robi (i informuje o tym) —
przydatne np. lokalnie, gdzie i tak masz już konto z `createsuperuser`.
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

        if not (username and email and password):
            self.stdout.write(
                "Pomijam — brak DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD w środowisku."
            )
            return

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Superuser '{username}' już istnieje — pomijam.")
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Utworzono superusera '{username}'."))
