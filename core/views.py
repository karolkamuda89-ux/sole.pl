import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ContactForm
from .models import Property

logger = logging.getLogger(__name__)


# Strona główna — obsługuje też POST z formularza kontaktowego (sekcja
# #kontakt w home.html): przy błędnych danych renderujemy tę samą stronę
# ponownie z wypełnionym formularzem i błędami pod polami (użytkownik nie
# traci wpisanej treści); przy poprawnych — zapis do bazy, próba wysyłki
# maila i przekierowanie (żeby odświeżenie strony nie wysłało formularza
# drugi raz).
def home(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            _send_contact_notification(contact_message)
            messages.success(
                request,
                "Dziękujemy za wiadomość! Odezwiemy się najszybciej, jak to możliwe.",
            )
            return redirect(reverse("core:home") + "#kontakt")
        messages.error(request, "Popraw zaznaczone pola formularza i spróbuj ponownie.")
    else:
        form = ContactForm()

    return render(request, "core/home.html", {"form": form})


def _send_contact_notification(contact_message):
    """Wysyła powiadomienie mailem na CONTACT_EMAIL. Zapis w bazie (już
    wykonany przed wywołaniem tej funkcji) jest tym, co się liczy — jeśli
    wysyłka maila się nie uda (np. brak/błędna konfiguracja SMTP), tylko
    logujemy błąd, zamiast wywalać zgłoszenie użytkownika błędem 500."""
    body = (
        f"Nowa wiadomość ze strony (formularz kontaktowy):\n\n"
        f"Imię i nazwisko: {contact_message.name}\n"
        f"E-mail: {contact_message.email}\n"
        f"Telefon: {contact_message.phone or '—'}\n"
        f"Temat: {contact_message.subject}\n\n"
        f"Wiadomość:\n{contact_message.message}"
    )
    try:
        send_mail(
            subject=f"[Strona] {contact_message.subject}",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Nie udało się wysłać powiadomienia e-mail o nowej wiadomości kontaktowej.")


# Lista ofert dla jednej lokalizacji — jeden widok obsługuje zarówno
# /oferta/polska/, jak i /oferta/teneryfa/ (parametr location w URL,
# core/urls.py). Kafelki renderuje core/oferta/lista.html, każdy linkuje
# do oferta_detail poniżej.
def oferta_lista(request, location):
    location_labels = dict(Property.LOCATION_CHOICES)
    if location not in location_labels:
        raise Http404("Nieznana lokalizacja")

    properties = (
        Property.objects.filter(location=location, is_published=True)
        .prefetch_related("images")
    )

    return render(
        request,
        "core/oferta/lista.html",
        {
            "location": location,
            "location_label": location_labels[location],
            "properties": properties,
        },
    )


# Podstrona pojedynczej oferty — jeden wspólny szablon (core/oferta/detail.html)
# dla WSZYSTKICH ofert. Nowa oferta dodana w adminie automatycznie dostaje
# tu swoją podstronę pod /oferta/<lokalizacja>/<slug>/ — nie trzeba nic
# dopisywać w kodzie, slug tworzy się sam z tytułu (patrz Property.save()).
def oferta_detail(request, location, slug):
    property_obj = get_object_or_404(
        Property.objects.prefetch_related("images"),
        location=location,
        slug=slug,
        is_published=True,
    )
    return render(request, "core/oferta/detail.html", {"property": property_obj})


# Polityka prywatności — treść przeniesiona z t1.sole.pl (patrz komentarz
# w szablonie), link do niej jest w stopce (base.html).
def polityka_prywatnosci(request):
    return render(request, "core/polityka-prywatnosci.html")
