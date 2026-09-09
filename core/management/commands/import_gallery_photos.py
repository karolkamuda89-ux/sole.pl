"""
Komenda: python manage.py import_gallery_photos

Po co: sekcja "Zobacz nasze realizacje" na stronie głównej (core/models.py:
GalleryPhoto) jest w pełni edytowalna w panelu /admin/. Ta komenda pilnuje,
żeby startowy zestaw 10 zdjęć (to, co wcześniej było na sztywno wpisane w
core/templates/core/home.html) zawsze faktycznie ISTNIAŁ NA DYSKU — na
Render dysk jest efemeryczny i znika przy KAŻDYM deployu, ale wiersze w
Postgresie zostają, więc bez tego po drugim deployu strona pokazywałaby
złamane obrazki (dokładnie to, co się stało: zaraz po wdrożeniu galerii
działała, a po kolejnym, niezwiązanym deployu — pliki zniknęły z dysku,
a komenda w starej wersji tylko sprawdzała "czy tabela jest pusta", więc
nic nie naprawiała).

Jak to NIE psuje zdjęć dodanych ręcznie w adminie:
Naprawiamy TYLKO wiersze, które nadal wyglądają jak nietknięty starter —
czyli mają dokładnie taki `order` i `alt_text` jak w STARTER_PHOTOS poniżej.
Jeśli admin podmienił zdjęcie na danej pozycji (inny plik, ale zwłaszcza
inny opis — w praktyce zawsze się różni) albo dodał zupełnie nowe wiersze,
te NIE są ruszane, nawet jeśli akurat brakuje im pliku na dysku (to ten sam
kompromis efemerycznego dysku co przy zdjęciach ofert — trzeba by wtedy
wgrać zdjęcie ponownie w panelu, nic nie da się z tym zrobić automatycznie,
bo oryginalne bajty custom zdjęcia istniały tylko na wymazanym dysku).
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
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
    help = "Dogrywa brakujące pliki startowego zestawu zdjęć galerii strony głównej."

    def handle(self, *args, **options):
        img_root = Path(settings.BASE_DIR) / "core" / "static" / "core" / "img"
        existing = {
            (p.order, p.alt_text): p for p in GalleryPhoto.objects.all()
        }

        healed = 0
        created = 0
        for order, rel_path, alt_text in STARTER_PHOTOS:
            source_path = img_root / rel_path
            match = existing.get((order, alt_text))

            if match:
                # default_storage.exists() (nie Path(...).exists()) - dziala
                # tak samo na lokalnym dysku i na Cloudflare R2/S3 (patrz
                # STORAGES w settings.py).
                if match.image and default_storage.exists(match.image.name):
                    continue  # nietknięty starter, plik jest na dysku — nic do zrobienia
                photo = match
                action = "Naprawiono"
                healed += 1
            else:
                if GalleryPhoto.objects.filter(order=order).exists():
                    # Ktoś w adminie podmienił zdjęcie/opis na tej pozycji —
                    # to już nie jest nietknięty starter, zostawiamy w spokoju.
                    continue
                photo = GalleryPhoto(order=order)
                action = "Dograno"
                created += 1

            if not source_path.exists():
                self.stderr.write(f"Pomijam — nie znaleziono {source_path}")
                continue

            photo.alt_text = alt_text
            with open(source_path, "rb") as file_obj:
                photo.image.save(source_path.name, File(file_obj), save=True)
            self.stdout.write(f"{action}: pozycja {order} — {alt_text[:50]}")

        self.stdout.write(self.style.SUCCESS(
            f"Galeria strony głównej: naprawiono {healed}, dograno nowych {created}."
        ))
