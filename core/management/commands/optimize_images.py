"""
Komenda: python manage.py optimize_images

Co robi:
1. Szuka zdjęć (jpg/jpeg/png) w core/static/core/img/raw/ — także w
   podfolderach, np. raw/galeria/, raw/hero/, dowolny podział jaki chcesz.
2. Zmniejsza je (jeśli są szersze niż --max-width) i zapisuje jako .webp
   w core/static/core/img/, zachowując ten sam układ podfolderów co w raw/
   (czyli raw/galeria/plaza.jpg -> core/img/galeria/plaza.webp).
3. Oryginały w raw/ zostają nietknięte — możesz tam trzymać źródłowe,
   ciężkie pliki, a do szablonów podpinasz już lekkie .webp.

Użycie:
    python manage.py optimize_images
    python manage.py optimize_images --quality 90 --max-width 2400
    python manage.py optimize_images --force   # nadpisz istniejące .webp

Przykład:
    Wrzuć zdjęcie do core/static/core/img/raw/hero.jpg, uruchom komendę,
    w core/static/core/img/hero.webp pojawi się zoptymalizowana wersja.
    W szablonie odwołujesz się do niej przez ścieżkę "core/img/hero.webp"
    (patrz {% static %} w home.html).
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image, ImageOps

# Formaty, które komenda potrafi wczytać i przekonwertować.
# .jfif to w praktyce JPEG pod inną nazwą (często z eksportu z telefonu/Messengera).
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".jfif"}


class Command(BaseCommand):
    help = "Konwertuje zdjęcia z core/static/core/img/raw/ do zoptymalizowanego formatu WebP."

    def add_arguments(self, parser):
        parser.add_argument(
            "--quality",
            type=int,
            default=82,
            help="Jakość kompresji WebP 1-100 (domyślnie 82 — dobry balans jakość/rozmiar).",
        )
        parser.add_argument(
            "--max-width",
            type=int,
            default=1920,
            help="Maksymalna szerokość w px — większe zdjęcia zostaną przeskalowane (domyślnie 1920).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Nadpisz plik .webp, nawet jeśli już istnieje.",
        )

    def handle(self, *args, quality, max_width, force, **options):
        raw_dir = Path(settings.BASE_DIR) / "core" / "static" / "core" / "img" / "raw"
        output_dir = raw_dir.parent

        if not raw_dir.exists():
            self.stderr.write(f"Nie znaleziono folderu: {raw_dir}")
            return

        # rglob("*") = szukaj też w podfolderach raw/, nie tylko na jego
        # pierwszym poziomie.
        source_files = sorted(
            p for p in raw_dir.rglob("*") if p.suffix.lower() in SUPPORTED_EXTENSIONS
        )

        if not source_files:
            self.stdout.write("Brak zdjęć do przetworzenia w core/static/core/img/raw/.")
            return

        for source_path in source_files:
            # Ścieżka względem raw/ (np. "galeria/plaza.jpg") — dzięki temu
            # podział na podfoldery odtwarza się jeden do jednego w core/img/.
            relative_path = source_path.relative_to(raw_dir)
            target_path = (output_dir / relative_path).with_suffix(".webp")

            if target_path.exists() and not force:
                self.stdout.write(f"Pomijam (już istnieje): {relative_path.with_suffix('.webp')} — użyj --force, by nadpisać.")
                continue

            target_path.parent.mkdir(parents=True, exist_ok=True)

            with Image.open(source_path) as img:
                # EXIF przechowuje orientację telefonów — bez tego zdjęcia
                # z aparatu potrafią wyjść "na leżąco".
                img = ImageOps.exif_transpose(img)

                # Zmniejszamy tylko za duże zdjęcia — nic nie tracimy jakościowo
                # w mniejszych plikach, a strona i tak nie wyświetli ich szerzej.
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_size = (max_width, round(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)

                # PNG bywa w trybie z paletą/przezroczystością — konwertujemy
                # do RGB, żeby zapis WebP zawsze się udał.
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")

                img.save(target_path, "WEBP", quality=quality, method=6)

            before_kb = source_path.stat().st_size / 1024
            after_kb = target_path.stat().st_size / 1024
            saved_pct = 100 - (after_kb / before_kb * 100) if before_kb else 0

            self.stdout.write(
                self.style.SUCCESS(
                    f"{relative_path} -> {relative_path.with_suffix('.webp')} "
                    f"({before_kb:.0f} KB -> {after_kb:.0f} KB, -{saved_pct:.0f}%)"
                )
            )
