"""
Komenda: python manage.py import_gallery_photos

Po co: sekcja "Zobacz nasze realizacje" na stronie głównej (core/models.py:
GalleryPhoto) jest teraz w pełni edytowalna w panelu /admin/, ale przy
pierwszym uruchomieniu strony tabela jest pusta — ta komenda wstawia
startowy zestaw 10 zdjęć (to, co wcześniej było na sztywno wpisane w
szablonie core/templates/core/home.html), żeby galeria od razu wyglądała
dobrze, zanim ktokolwiek zacznie ją edytować w panelu.

WAŻNE — dlaczego to NIE jest self-healing jak import_apartments:
Property ma stabilną tożsamość (slug), więc import_apartments może
bezpiecznie podmieniać same zdjęcia bez ruszania reszty danych oferty.
GalleryPhoto to płaska lista bez takiej tożsamości — gdyby ta komenda przy
KAŻDYM starcie sprawdzała "czy pliki są na dysku" i w razie braku czyściła
tabelę, wywaliłaby też zdjęcia, które ktoś ręcznie dodał w adminie (a nie
tylko te ze startowego zestawu). Dlatego działa tylko RAZ — jeśli w tabeli
jest już cokolwiek, zostawia to w spokoju, nawet jeśli pliki akurat zniknęły
z dysku (to ten sam, znany kompromis efemerycznego dysku na Render co przy
zdjęciach ofert — patrz komentarz przy MEDIA_ROOT w settings.py). W takim
wypadku trzeba po prostu wgrać brakujące zdjęcie ponownie w panelu.
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from core.models import GalleryPhoto

# (kolejność, ścieżka względem core/static/core/img/, opis alternatywny)
STARTER_PHOTOS = [
    (0, "ap1/IMG-20260816-WA0000.webp", "Elegancki salon z okrągłym czarnym stołem, tapicerowanymi fotelami i marmurową ścianą w apartamencie na Teneryfie"),
    (1, "ap4/01.webp", "Przestronny, jasny salon połączony z kuchnią w nowoczesnym wykończeniu"),
    (2, "ap3/IMG-20260709-WA0000.webp", "Umeblowany taras z fotelami wypoczynkowymi, stolikiem i zielenią w donicach"),
    (3, "ap2/IMG-20251208-WA0003.webp", "Luksusowa łazienka wykończona beżowym marmurem, z owalną umywalką i złotą baterią"),
    (4, "ap7/IMG-20260813-WA0016.webp", "Taras na dachu o zachodzie słońca z widokiem na góry Teneryfy i leżakami"),
    (5, "ap6/IMG-20260710-WA0000.webp", "Nowoczesna kuchnia z orzechową zabudową i okrągłym stołem jadalnym"),
    (6, "ap3/IMG-20260709-WA0010.webp", "Stylowa jadalnia z designerską lampą sufitową i ciemnym okrągłym stołem"),
    (7, "ap5/IMG-20260802-WA0010.webp", "Widok z góry na przestronny taras apartamentu z bujną roślinnością"),
    (8, "ap6/IMG-20260710-WA0015.webp", "Zadaszony taras wypoczynkowy z widokiem na sypialnię apartamentu"),
    (9, "ap7/IMG-20260813-WA0020.webp", "Elegancka łazienka z okrągłym lustrem i przeszkloną kabiną prysznicową"),
]


class Command(BaseCommand):
    help = "Wstawia startowy zestaw zdjęć galerii strony głównej, jeśli tabela jest jeszcze pusta."

    def handle(self, *args, **options):
        if GalleryPhoto.objects.exists():
            self.stdout.write(
                "Galeria strony głównej ma już zdjęcia (panel admina jest tu źródłem "
                "prawdy) — pomijam."
            )
            return

        img_root = Path(settings.BASE_DIR) / "core" / "static" / "core" / "img"
        created = 0
        for order, rel_path, alt_text in STARTER_PHOTOS:
            source_path = img_root / rel_path
            if not source_path.exists():
                self.stderr.write(f"Pomijam — nie znaleziono {source_path}")
                continue
            with open(source_path, "rb") as file_obj:
                photo = GalleryPhoto(alt_text=alt_text, order=order)
                photo.image.save(source_path.name, File(file_obj), save=True)
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Galeria strony głównej: dograno {created} zdjęć."))
