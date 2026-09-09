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
# patrz convert_uploaded_image_to_webp() niżej.
UPLOAD_MAX_WIDTH = 1920
UPLOAD_WEBP_QUALITY = 82


def convert_uploaded_image_to_webp(image_field):
    """Dociska zdjęcie do UPLOAD_MAX_WIDTH i zwraca jego wersję WebP jako
    ContentFile — wspólna logika dla PropertyImage i GalleryPhoto, żeby nie
    trzymać dwóch kopii tego samego kodu konwersji Pillow."""
    image_field.seek(0)
    img = Image.open(image_field)
    img = ImageOps.exif_transpose(img)

    if img.width > UPLOAD_MAX_WIDTH:
        ratio = UPLOAD_MAX_WIDTH / img.width
        img = img.resize((UPLOAD_MAX_WIDTH, round(img.height * ratio)), Image.LANCZOS)

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    buffer = io.BytesIO()
    img.save(buffer, "WEBP", quality=UPLOAD_WEBP_QUALITY, method=6)
    buffer.seek(0)

    new_name = f"{Path(image_field.name).stem}.webp"
    return ContentFile(buffer.read(), name=new_name)


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
    CURRENCY_CHOICES = [
        ("PLN", "PLN (zł)"),
        ("EUR", "EUR (€)"),
    ]
    CURRENCY_SYMBOLS = {"PLN": "zł", "EUR": "€"}

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
    price = models.DecimalField("Cena", max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField("Waluta", max_length=3, choices=CURRENCY_CHOICES, default="PLN")
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

    @property
    def currency_symbol(self):
        """Symbol do wyświetlenia obok ceny na stronie (patrz oferta/lista.html
        i oferta/detail.html) — zamiast powtarzać ten sam if/else w dwóch
        szablonach, jedno miejsce decyduje, jak wygląda dana waluta."""
        return self.CURRENCY_SYMBOLS.get(self.currency, self.currency)

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
    """Jedno zdjęcie w galerii oferty. `alt_text` jest OPCJONALNY w formularzu
    (blank=True) — jeśli formularz wymagał go przy KAŻDYM zdjęciu, a ktoś
    wgrywał kilkanaście naraz i pominął jedno pole, cały formularz odrzucał
    zapis z błędem walidacji, a przeglądarka (nie Django) czyści przy tym
    wybrane pliki w polach typu "file" — trzeba było wybierać zdjęcia od
    nowa. Zamiast wymuszać wypełnienie, save() niżej sam dogeneruje sensowny
    opis, gdy zostanie puste."""

    property = models.ForeignKey(
        Property, related_name="images", on_delete=models.CASCADE, verbose_name="Oferta"
    )
    image = models.ImageField("Zdjęcie", upload_to=property_image_upload_to)
    alt_text = models.CharField(
        "Opis alternatywny (SEO)", max_length=250, blank=True,
        help_text="Możesz zostawić puste — zostanie dogenerowany automatycznie.",
    )
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
        # Puste alt_text (patrz komentarz w klasie wyżej, dlaczego pole jest
        # opcjonalne) — dogeneruj coś konkretniejsze niż nic. `refresh_alt_text`
        # (uruchamiane przy każdym deployu, patrz start.sh) i tak ponumeruje
        # to porządnie później ("... — zdjęcie N z M"), więc to tylko
        # rozsądny placeholder na czas między wgraniem a najbliższym deployem.
        if not self.alt_text and self.property_id:
            self.alt_text = f"{self.property.title} {self.property.location_phrase()}"

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

        # Tylko JEDNO zdjęcie główne na ofertę — bez tego zaznaczenie nowego
        # "Zdjęcie główne" bez ręcznego odznaczenia starego dawało DWA
        # wpisy z is_cover=True, a Property.cover_image i tak wybierał ten
        # z niższym `order`/id, czyli często wciąż stary. Odznaczamy resztę
        # PO zapisie (nie przed), żeby to zdjęcie na pewno już miało nadane id.
        if self.is_cover:
            PropertyImage.objects.filter(property=self.property, is_cover=True).exclude(
                pk=self.pk
            ).update(is_cover=False)

    def _convert_image_to_webp(self):
        try:
            self.image = convert_uploaded_image_to_webp(self.image)
        except Exception:
            # Nietypowy/uszkodzony plik — zamiast wywalać zapis całego
            # formularza w adminie błędem 500, zostawiamy oryginał
            # nieprzekonwertowany i tylko odnotowujemy to w logu.
            logger.exception("Nie udało się przekonwertować zdjęcia oferty na WebP.")


def gallery_photo_upload_to(instance, filename):
    return f"galeria/{filename}"


class GalleryPhoto(models.Model):
    """Zdjęcia sekcji "Zobacz nasze realizacje" na stronie głównej (patrz
    core/templates/core/home.html, .airbnb-gallery-grid) — edytowalne z
    panelu admina zamiast na sztywno w szablonie. Kolejność (`order`)
    decyduje o układzie: 1. zdjęcie = duży kafelek, 2.-5. = małe kafelki
    w widocznej siatce, kolejne = tylko dodatkowe slajdy w lightboksie
    (widoczne po kliknięciu "Pokaż wszystkie zdjęcia")."""

    image = models.ImageField("Zdjęcie", upload_to=gallery_photo_upload_to)
    # blank=True — patrz komentarz przy PropertyImage.alt_text: wymagane pole
    # tekstowe przy formularzu z uploadem plików oznacza, że błąd walidacji
    # (np. puste pole przy jednym z kilku wgrywanych na raz zdjęć) czyści
    # wybrane pliki w przeglądarce i trzeba wybierać je od nowa.
    alt_text = models.CharField(
        "Opis alternatywny (SEO)", max_length=250, blank=True,
        help_text="Możesz zostawić puste — zostanie dogenerowany automatycznie.",
    )
    order = models.PositiveIntegerField(
        "Kolejność", default=0,
        help_text="0 = duże zdjęcie, 1-4 = małe kafelki w siatce, wyższe = tylko w powiększeniu.",
    )

    class Meta:
        verbose_name = "Zdjęcie galerii (strona główna)"
        verbose_name_plural = "Zdjęcia galerii (strona główna)"
        ordering = ["order", "id"]

    def __str__(self):
        return self.alt_text or self.image.name

    def save(self, *args, **kwargs):
        # Puste alt_text — dogeneruj coś konkretniejsze niż nic (patrz
        # komentarz przy polu wyżej). Ta galeria nie ma osobnej komendy typu
        # refresh_alt_text, która by to później ponumerowała, więc fallback
        # dostaje numer kolejności od razu, żeby nie duplikować identycznego
        # opisu na wielu zdjęciach naraz.
        if not self.alt_text:
            self.alt_text = f"Zdjęcie z realizacji Sole na Teneryfie — pozycja {self.order}"

        if self.image and not self.image.name.lower().endswith(".webp"):
            try:
                self.image = convert_uploaded_image_to_webp(self.image)
            except Exception:
                logger.exception("Nie udało się przekonwertować zdjęcia galerii na WebP.")
        super().save(*args, **kwargs)


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
