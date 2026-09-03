from django.conf import settings


def meta_pixel(request):
    """Udostępnia META_PIXEL_ID (settings.py) każdemu szablonowi jako
    zmienną {{ META_PIXEL_ID }} — używa jej base.html, żeby zdecydować,
    czy w ogóle warto ładować skrypt zgody na cookies z Pixelem."""
    return {"META_PIXEL_ID": settings.META_PIXEL_ID}
