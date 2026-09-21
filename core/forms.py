import time

from django import forms

from .models import ContactMessage

# Poniżej ilu sekund od wyrenderowania formularza uznajemy wysyłkę za
# podejrzaną (boty wypełniają i wysyłają formularz praktycznie natychmiast,
# człowiekowi zajmuje to zawsze co najmniej kilka sekund).
MIN_SUBMIT_SECONDS = 3


class ContactForm(forms.ModelForm):
    """Formularz z sekcji Kontakt na stronie głównej. To ModelForm oparty
    o ContactMessage — walidacja i lista pól idą wprost z modelu, więc
    dodanie/zmiana pola w models.py wystarczy, nie trzeba duplikować tu.

    Dwa dodatkowe pola (website, form_rendered_at) NIE są częścią modelu —
    to filtr antyspamowy, patrz komentarze przy każdym z nich i przy clean().
    Wykryty spam nie podnosi błędu walidacji (to by tylko uczyło boty, że
    coś jest nie tak, i mogłoby niepotrzebnie zablokować prawdziwego
    użytkownika w skrajnym przypadku) — zamiast tego core.views.home()
    sprawdza is_spam() po udanej walidacji i po prostu nie zapisuje/nie
    wysyła wiadomości, ale POKAZUJE tę samą stronę z podziękowaniem, żeby
    bot "myślał", że mu się udało i nie próbował dalej."""

    # Honeypot — pole niewidoczne dla człowieka (ukryte w CSS, patrz
    # core/static/core/css/style.css, klasa .hp-field), ale boty wypełniające
    # formularze "na oślep" (po nazwie pola, nie po tym co widać na ekranie)
    # bardzo często je wypełniają. Zwykły widget=TextInput, NIE HiddenInput —
    # pole type="hidden" jest tak oczywistym trikiem, że rozpoznaje go nawet
    # prosty bot i go pomija; zwykłe pole tekstowe ukryte przez CSS nie.
    website = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(attrs={
            "class": "hp-field",
            "tabindex": "-1",
            "autocomplete": "off",
        }),
    )
    # Znacznik czasu (sekundy epoch) wygenerowania formularza — ustawiany
    # jako initial w core/views.py przy GET. Boty zwykle wysyłają formularz
    # w mniej niż sekundę od wczytania strony (nie "czytają" jej), człowiek
    # potrzebuje na to zawsze kilku sekund.
    form_rendered_at = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Jan Kowalski"}),
            "email": forms.EmailInput(attrs={"placeholder": "jan@przyklad.pl"}),
            "phone": forms.TextInput(attrs={"placeholder": "+48 600 000 000"}),
            "subject": forms.TextInput(attrs={"placeholder": "Np. Pytanie o Apartament 3"}),
            "message": forms.Textarea(attrs={"placeholder": "Treść wiadomości..."}),
        }

    def is_spam(self):
        """Woła się TYLKO po is_valid() (potrzebuje self.cleaned_data).
        Nie jest częścią clean() — spam to nie błąd walidacji, patrz
        komentarz w docstringu klasy."""
        if self.cleaned_data.get("website"):
            return True

        rendered_at = self.cleaned_data.get("form_rendered_at")
        if not rendered_at:
            return True  # pole zmanipulowane/usunięte — też podejrzane
        try:
            elapsed = time.time() - float(rendered_at)
        except (TypeError, ValueError):
            return True
        return elapsed < MIN_SUBMIT_SECONDS
