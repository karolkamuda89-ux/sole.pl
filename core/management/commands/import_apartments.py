"""
Komenda: python manage.py import_apartments

Co robi:
Tworzy w bazie 7 ofert ("Apartament 1"–"Apartament 7", lokalizacja
Teneryfa) i podpina pod każdą wszystkie zdjęcia .webp z odpowiedniego
folderu core/static/core/img/apN/ jako galerię (PropertyImage) — kopiując
je do MEDIA_ROOT (media/oferty/...), bo tam admin trzyma zdjęcia ofert.

WAŻNE — dlaczego to sprawdza pliki na dysku, nie tylko wpis w bazie:
Na Render (i podobnych hostingach z efemerycznym dyskiem) baza danych
(Postgres) przeżywa między deployami, ale PLIKI na dysku — nie. Gdyby ta
komenda tylko sprawdzała "czy oferta 'Apartament 3' już jest w bazie", to
po drugim deployu wpis by był (bo baza pamięta), ale prawdziwe pliki
zdjęć by zniknęły (nowy, pusty dysk) — strona pokazywałaby złamane
obrazki. Dlatego sprawdzamy, czy PLIK okładki faktycznie istnieje na
dysku — jeśli nie, dogrywamy zdjęcia od nowa, nawet jeśli oferta w bazie
już jest (jej pozostałe pola — cena, opis itd. — zostają nietknięte).

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
    python manage.py import_apartments --force   # dogrywa zdjęcia, nawet jeśli są już na dysku
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from core.models import Property, PropertyImage

APARTMENT_NUMBERS = range(1, 8)  # ap1 .. ap7
SUPPORTED_EXTENSIONS = {".webp"}


class Command(BaseCommand):
    help = "Tworzy w bazie oferty Apartament 1-7 i dogrywa ich zdjęcia, jeśli brakuje ich na dysku."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Skopiuj zdjęcia od nowa, nawet jeśli już są na dysku.",
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

            # get_or_create zamiast "sprawdź i utwórz" — jeśli oferta już
            # istnieje (np. ktoś zmienił jej cenę/opis w panelu), zostaje
            # BEZ ZMIAN. Nowa powstaje tylko przy pierwszym uruchomieniu.
            property_obj, _ = Property.objects.get_or_create(
                slug=slug,
                defaults=dict(
                    title=title,
                    location="teneryfa",
                    description="Opis apartamentu — do uzupełnienia w panelu administratora.",
                    status="dostepny",
                ),
            )

            cover = property_obj.images.filter(is_cover=True).first()
            cover_file_exists = bool(cover and cover.image and Path(cover.image.path).exists())

            if cover_file_exists and not force:
                self.stdout.write(f"Pomijam {title} — zdjęcia już są na dysku.")
                continue

            # Wpisy PropertyImage bez pliku pod spodem są bezużyteczne
            # (złamany obrazek na stronie) — czyścimy je przed ponownym
            # skopiowaniem. Sama oferta (Property) zostaje nietknięta.
            property_obj.images.all().delete()

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
                self.style.SUCCESS(f"{title}: dograno {len(photos)} zdjęć.")
            )
