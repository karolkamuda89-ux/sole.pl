from django.contrib import admin
from django.utils.html import format_html

from .models import ContactMessage, Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    """Galeria zdjęć wyświetlana bezpośrednio pod formularzem oferty,
    zamiast osobnego ekranu — łatwiej dodać/usunąć/przesortować zdjęcia
    jednej nieruchomości w jednym miejscu."""

    model = PropertyImage
    extra = 1
    fields = ("preview", "image", "alt_text", "order", "is_cover")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.image:
            # loading="lazy" — przy ofertach z kilkudziesięcioma zdjęciami
            # (jak Apartament 7, 47 sztuk) przeglądarka bez tego odpalała
            # WSZYSTKIE miniatury na raz przy otwarciu formularza; pod
            # słabszym łączem/serwerem deweloperskim część takich żądań
            # potrafiła się wysypać (502). Lazy loading każe przeglądarce
            # doczytywać miniatury dopiero przy przewijaniu do nich.
            return format_html(
                '<img src="{}" loading="lazy" style="height:60px;border-radius:6px;object-fit:cover;">',
                obj.image.url,
            )
        return "—"

    preview.short_description = "Podgląd"


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("title", "location", "price", "area_m2", "rooms", "status", "is_published")
    # Cenę (i te dwa pola) da się edytować wprost na liście ofert — bez
    # wchodzenia w każdą osobno. Uwaga: pole editable nie może być pierwsze
    # w list_display (Django wymaga, żeby pierwsza kolumna była linkiem
    # do formularza), stąd "title" zostaje samym linkiem.
    list_editable = ("price", "area_m2", "rooms")
    list_filter = ("location", "status", "is_published")
    search_fields = ("title", "description")
    # Slug uzupełnia się sam w adminie na podstawie tytułu (JS w przeglądarce) —
    # widać/edytuje się go, ale nie trzeba wpisywać ręcznie.
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PropertyImageInline]
    # Pogrupowanie pól na formularzu — samych pól nic to nie zmienia
    # (wciąż widoczne są wszystkie z modelu), tylko czytelniej je
    # rozkłada, bo oferta ma już sporo szczegółowych informacji.
    # Te sekcje odpowiadają 1:1 czterem sekcjom opisowym na stronie oferty
    # (patrz core/templates/core/oferta/detail.html): Opis nieruchomości,
    # Powierzchnia, Zalety, Wyposażenie.
    fieldsets = (
        ("Podstawowe informacje", {
            "fields": ("title", "slug", "location", "address", "status", "is_published"),
        }),
        ("Parametry", {
            "fields": ("price", "area_m2", "rooms", "bathrooms"),
        }),
        ("Opis nieruchomości", {
            "fields": ("description",),
        }),
        ("Powierzchnia", {
            "fields": ("area_details",),
        }),
        ("Zalety", {
            "fields": ("advantages",),
        }),
        ("Wyposażenie", {
            "fields": ("amenities",),
        }),
    )


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "phone", "created_at", "is_read")
    # Zaznaczenie "przeczytana" wprost na liście — to jedyne pole, które ma
    # sens edytować (treść wiadomości od odwiedzającego zostaje tylko do
    # odczytu, patrz readonly_fields niżej).
    list_editable = ("is_read",)
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "phone", "subject", "message", "created_at")
