import io
import logging
from pathlib import Path

from django.core.files.base import ContentFile
from django.db import models
from django.utils.text import slugify
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Te same wartości domyślne co core/management/commands/optimize_images.py
# (skrypt do core/static/core/img/raw/) — zdjęcia wgrywane przez panel
# admina przechodzą tę samą obróbkę, tylko automatycznie przy zapisie,
# patrz PropertyImage.save() niżej.
UPLOAD_MAX_WIDTH = 1920
UPLOAD_WEBP_QUALITY = 82


class Property(models.Model):
    """Pojedyncza oferta nieruchomości (np. jeden apartament). Edytowalna
    w panelu administratora — zdjęcia dopina się osobno przez PropertyImage
    (widoczne w adminie jako sekcja "Zdjęcia" pod formularzem oferty)."""

    LOCATION_CHOICES = [
        ("polska", "Polska"),
        ("teneryfa", "Teneryfa"),
    ]
    STATUS_CHOICES = [
        ("dostepny", "Dostępny"),
        ("zarezerwowany", "Zarezerwowany"),
        ("sprzedany", "Sprzedany"),
    ]

    title = models.CharField("Tytuł", max_length=200)
    # Puste przy tworzeniu w kodzie (patrz save()) — w adminie wypełnia się
    # automatycznie z tytułu dzięki prepopulated_fields w PropertyAdmin.
    slug = models.SlugField("Adres URL (slug)", unique=True, blank=True)
    location = models.CharField("Lokalizacja", max_length=20, choices=LOCATION_CHOICES)
    # Dokładniejsza lokalizacja niż samo Polska/Teneryfa — pokazuje się pod
    # tytułem na podstronie szczegółów oferty, np. "Costa Adeje, Teneryfa".
    address = models.CharField("Adres / okolica", max_length=200, blank=True)
    # Strona oferty ma 4 osobne sekcje opisowe — description/area_details
    # to zwykły tekst, advantages/amenities to listy (jedna pozycja na
    # linię, patrz *_list() niżej). Puste pole po prostu nie pokazuje
    # swojej sekcji na stronie.
    description = models.TextField("Opis nieruchomości", blank=True)
    price = models.DecimalField("Cena (EUR)", max_digits=10, decimal_places=2, null=True, blank=True)
    area_m2 = models.DecimalField("Powierzchnia (m²)", max_digits=6, decimal_places=1, null=True, blank=True)
    area_details = models.TextField(
        "Powierzchnia — opis", blank=True,
        help_text='Rozbicie powierzchni, np. "43,8 m² salon + 25,6 m² taras". Liczba z pola wyżej i tak zawsze pokazuje się w zestawieniu parametrów.',
    )
    rooms = models.PositiveSmallIntegerField("Liczba pokoi", null=True, blank=True)
    bathrooms = models.PositiveSmallIntegerField("Liczba łazienek", null=True, blank=True)
    advantages = models.TextField(
        "Zalety (jedna na linię)", blank=True,
        help_text="Każda linia to jeden punkt na liście zalet na stronie oferty.",
    )
    amenities = models.TextField(
        "Wyposażenie (jedno na linię)", blank=True,
        help_text="Każda linia to jeden punkt na liście wyposażenia na stronie oferty.",
    )
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default="dostepny")
    # Odznaczenie w adminie chowa ofertę ze strony bez jej usuwania —
    # przydatne np. gdy nieruchomość jest wycofana, ale dane mają zostać.
    is_published = models.BooleanField("Opublikowana", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Oferta"
        verbose_name_plural = "Oferty"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("core:oferta_detail", kwargs={"location": self.location, "slug": self.slug})

    @property
    def cover_image(self):
        """Zdjęcie główne (kafelek na liście + góra strony szczegółów).
        Bierze to oznaczone is_cover=True w adminie, a jak nikt tego nie
        zaznaczył — po prostu pierwsze zdjęcie w kolejności."""
        return self.images.filter(is_cover=True).first() or self.images.first()

    # Polska odmiana: "w Polsce", ale "na Teneryfie" — różny przyimek I
    # przypadek dla różnych miejsc, więc get_location_display() (zwraca
    # mianownik: "Polska"/"Teneryfa") nie nadaje się wprost do zdania typu
    # "Apartament X na {lokalizacja}". Używane w alt_text zdjęć (patrz
    # core/management/commands/import_apartments.py i refresh_alt_text.py).
    LOCATION_PHRASES = {
        "polska": "w Polsce",
        "teneryfa": "na Teneryfie",
    }

    def location_phrase(self):
        return self.LOCATION_PHRASES.get(self.location, self.get_location_display())

    def amenities_list(self):
        """Rozbija pole `amenities` (jedna pozycja na linię) na listę do
        wyświetlenia w szablonie — puste linie są pomijane."""
        return [line.strip() for line in self.amenities.splitlines() if line.strip()]

    def advantages_list(self):
        """To samo co amenities_list(), tylko dla pola `advantages`."""
        return [line.strip() for line in self.advantages.splitlines() if line.strip()]


def property_image_upload_to(instance, filename):
    return f"oferty/{instance.property.slug}/{filename}"


class PropertyImage(models.Model):
    """Jedno zdjęcie w galerii oferty. `alt_text` jest wymagany — to on
    trafia do atrybutu alt na stronie (SEO/dostępność), więc w adminie
    warto go od razu wypełnić czymś konkretnym, nie zostawiać pustego."""

    property = models.ForeignKey(
        Property, related_name="images", on_delete=models.CASCADE, verbose_name="Oferta"
    )
    image = models.ImageField("Zdjęcie", upload_to=property_image_upload_to)
    alt_text = models.CharField("Opis alternatywny (SEO)", max_length=250)
    # Kolejność wyświetlania w galerii — mniejsza liczba = wyżej/wcześniej.
    order = models.PositiveIntegerField("Kolejność", default=0)
    is_cover = models.BooleanField("Zdjęcie główne", default=False)

    class Meta:
        verbose_name = "Zdjęcie oferty"
        verbose_name_plural = "Zdjęcia oferty"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.property.title} — {self.alt_text or self.image.name}"

    def save(self, *args, **kwargs):
        # Nowo wgrane zdjęcie (jeszcze nie .webp) — dociśnij do rozsądnego
        # rozmiaru i zamień na WebP, dokładnie jak optimize_images robi to
        # dla core/static/core/img/raw/. Osoba w panelu admina nie musi
        # pamiętać o konwersji — wrzuca jpg/png z telefonu, tu i tak
        # wyląduje jako lekki .webp. Plik, który już JEST .webp (np. z
        # `import_apartments`), zostaje nietknięty — nie przeliczamy go
        # przy każdym zapisie formularza.
        if self.image and not self.image.name.lower().endswith(".webp"):
            self._convert_image_to_webp()
        super().save(*args, **kwargs)

    def _convert_image_to_webp(self):
        try:
            self.image.seek(0)
            img = Image.open(self.image)
            img = ImageOps.exif_transpose(img)

            if img.width > UPLOAD_MAX_WIDTH:
                ratio = UPLOAD_MAX_WIDTH / img.width
                img = img.resize((UPLOAD_MAX_WIDTH, round(img.height * ratio)), Image.LANCZOS)

            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

            buffer = io.BytesIO()
            img.save(buffer, "WEBP", quality=UPLOAD_WEBP_QUALITY, method=6)
            buffer.seek(0)

            new_name = f"{Path(self.image.name).stem}.webp"
            self.image = ContentFile(buffer.read(), name=new_name)
        except Exception:
            # Nietypowy/uszkodzony plik — zamiast wywalać zapis całego
            # formularza w adminie błędem 500, zostawiamy oryginał
            # nieprzekonwertowany i tylko odnotowujemy to w logu.
            logger.exception("Nie udało się przekonwertować zdjęcia oferty na WebP.")


class ContactMessage(models.Model):
    """Wiadomość wysłana przez formularz kontaktowy na stronie głównej
    (core.views.contact_submit). Zapisywana w bazie ORAZ wysyłana mailem
    na CONTACT_EMAIL (settings.py) — zapis do bazy jest tym, co się liczy
    (widać ją zawsze w adminie), wysyłka maila to tylko dodatkowe
    powiadomienie i może się nie udać bez wpływu na sam zapis."""

    name = models.CharField("Imię i nazwisko", max_length=150)
    email = models.EmailField("Adres e-mail")
    phone = models.CharField("Telefon", max_length=30, blank=True)
    subject = models.CharField("Temat", max_length=200)
    message = models.TextField("Wiadomość")
    created_at = models.DateTimeField(auto_now_add=True)
    # Zaznaczane ręcznie w adminie, gdy ktoś już odpowiedział/obsłużył
    # zapytanie — pomaga odróżnić nowe wiadomości od załatwionych.
    is_read = models.BooleanField("Przeczytana", default=False)

    class Meta:
        verbose_name = "Wiadomość kontaktowa"
        verbose_name_plural = "Wiadomości kontaktowe"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} — {self.name}"
