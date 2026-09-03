from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """Formularz z sekcji Kontakt na stronie głównej. To ModelForm oparty
    o ContactMessage — walidacja i lista pól idą wprost z modelu, więc
    dodanie/zmiana pola w models.py wystarczy, nie trzeba duplikować tu."""

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
