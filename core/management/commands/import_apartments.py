"""
Komenda: python manage.py import_apartments

Co robi:
Tworzy w bazie 7 ofert ("Apartament 1"–"Apartament 7", lokalizacja
Teneryfa) i podpina pod każdą wszystkie zdjęcia .webp z odpowiedniego
folderu core/static/core/img/apN/ jako galerię (PropertyImage) — kopiując
je do MEDIA_ROOT (media/oferty/...), bo tam admin trzyma zdjęcia ofert.

Cena, powierzchnia i liczba pokoi zostają puste — to prawdziwe dane, które
uzupełnia się ręcznie w panelu administratora. Opis to placeholder do
podmiany. `alt_text` każdego zdjęcia jest generyczny, ale ponumerowany
("Apartament 3 na Teneryfie — zdjęcie 12 z 44") — nie opisuje dokładnie
TEGO zdjęcia, ale każde ma inny tekst (ważne pod SEO — identyczny alt na
kilkudziesięciu zdjęciach z rzędu wygląda źle). Jeśli chcesz dopracować
opis pod konkretne, najważniejsze zdjęcia (np. okładkę), zrób to ręcznie
w panelu — resztę (setki zdjęć) nie ma sensu opisywać z osobna.

Użycie:
    python manage.py import_apartments
    python manage.py import_apartments --force   # nadpisz istniejące oferty
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from core.models import Property, PropertyImage

APARTMENT_NUMBERS = range(1, 8)  # ap1 .. ap7
SUPPORTED_EXTENSIONS = {".webp"}


class Command(BaseCommand):
    help = "Tworzy w bazie oferty Apartament 1-7 na podstawie zdjęć z core/static/core/img/apN/."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Usuń i utwórz od nowa ofertę, jeśli już istnieje (dotyczy też jej zdjęć).",
        )

    def handle(self, *args, force, **options):
        img_root = Path(settings.BASE_DIR) / "core" / "static" / "core" / "img"

        for n in APARTMENT_NUMBERS:
            title = f"Apartament {n}"
            slug = f"apartament-{n}"
            source_dir = img_root / f"ap{n}"

            if not source_dir.exists():
                self.stderr.write(f"Pomijam {title} — nie znaleziono folderu {source_dir}")
                continue

            existing = Property.objects.filter(slug=slug).first()
            if existing:
                if not force:
                    self.stdout.write(f"Pomijam {title} — już istnieje w bazie (użyj --force, by nadpisać).")
                    continue
                existing.delete()

            property_obj = Property.objects.create(
                title=title,
                slug=slug,
                location="teneryfa",
                description="Opis apartamentu — do uzupełnienia w panelu administratora.",
                status="dostepny",
            )

            photos = sorted(
                p for p in source_dir.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS
            )

            total = len(photos)
            for index, photo_path in enumerate(photos):
                with open(photo_path, "rb") as file_obj:
                    image = PropertyImage(
                        property=property_obj,
                        # Numer w opisie — bez tego wszystkie zdjęcia jednego
                        # apartamentu miałyby DOKŁADNIE ten sam alt, co jest
                        # złe pod SEO (zduplikowana treść). To wciąż prosty,
                        # automatyczny opis — nie ręczne opisywanie każdego
                        # z osobna, na co przy setkach zdjęć nie ma szans.
                        alt_text=f"{title} {property_obj.location_phrase()} — zdjęcie {index + 1} z {total}",
                        order=index,
                        is_cover=(index == 0),
                    )
                    image.image.save(photo_path.name, File(file_obj), save=True)

            self.stdout.write(
                self.style.SUCCESS(f"{title}: utworzono ofertę i dodano {len(photos)} zdjęć.")
            )
