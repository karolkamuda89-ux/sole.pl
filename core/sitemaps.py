"""Mapa strony pod /sitemap.xml (patrz config/urls.py) — pomaga Google
szybciej odnaleźć i zaindeksować wszystkie podstrony, zamiast liczyć na to,
że sam je znajdzie, klikając linki. Klasy Sitemap poniżej NIE wymagają
django.contrib.sites — widok sitemap() sam buduje domenę z request.get_host(),
więc na Render/ngrok/lokalnie zawsze wskazuje na właściwy adres bez żadnej
dodatkowej konfiguracji."""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Property


class StaticViewSitemap(Sitemap):
    """Strony bez własnego modelu w bazie — strona główna i polityka
    prywatności. Nowa "stała" podstrona (np. przyszłe "O nas" jako osobny
    URL) dopisuje się tu jednym wpisem w items()."""

    priority = 0.6
    changefreq = "monthly"

    def items(self):
        return ["core:home", "core:polityka_prywatnosci"]

    def location(self, item):
        return reverse(item)


class OfertaListaSitemap(Sitemap):
    """Dwie listy ofert (Polska/Teneryfa) — patrz Property.LOCATION_CHOICES."""

    priority = 0.7
    changefreq = "daily"

    def items(self):
        return [value for value, _ in Property.LOCATION_CHOICES]

    def location(self, item):
        return reverse("core:oferta_lista", kwargs={"location": item})


class PropertySitemap(Sitemap):
    """Podstrona każdej opublikowanej oferty — ciągnie się wprost z bazy,
    więc nowa oferta dodana w panelu admina pojawia się tu sama, nic nie
    trzeba ręcznie dopisywać."""

    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Property.objects.filter(is_published=True)

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.updated_at
