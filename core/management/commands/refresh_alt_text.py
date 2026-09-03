"""
Komenda: python manage.py refresh_alt_text

Po co: `import_apartments` generuje alt_text tylko dla NOWO tworzonych
zdjęć — apartamenty, które już są w bazie (czyli w praktyce wszystkie po
pierwszym uruchomieniu), nigdy przez nią więcej nie przechodzą. Ta komenda
dogania istniejące zdjęcia do aktualnego wzoru bez ruszania samych plików
ani żadnych innych pól (cena, opis itd. zostają nietknięte).

Bezpieczna do uruchamiania wielokrotnie — po prostu ustawia ten sam,
przewidywalny tekst za każdym razem (patrz build.sh — jest tam na stałe,
więc każdy kolejny deploy sam to utrzyma w porządku, nawet po dodaniu
nowych zdjęć w panelu).
"""

from django.core.management.base import BaseCommand

from core.models import Property


class Command(BaseCommand):
    help = "Ustawia ponumerowany alt_text ('<Tytuł> — zdjęcie N z M') na wszystkich zdjęciach ofert."

    def handle(self, *args, **options):
        updated = 0
        for property_obj in Property.objects.prefetch_related("images"):
            images = list(property_obj.images.all())  # kolejność z Meta.ordering (order, id)
            total = len(images)
            for index, image in enumerate(images):
                new_alt = f"{property_obj.title} {property_obj.location_phrase()} — zdjęcie {index + 1} z {total}"
                if image.alt_text != new_alt:
                    image.alt_text = new_alt
                    image.save(update_fields=["alt_text"])
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Zaktualizowano alt_text dla {updated} zdjęć."))
