from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Główny router projektu — /admin/ to panel administracyjny Django,
# wszystko inne (na razie tylko "/") obsługuje aplikacja core (core/urls.py).
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]

# Serwowanie zdjęć wgranych przez admina (MEDIA_ROOT) — tylko w trybie
# deweloperskim; na produkcji zajmuje się tym serwer WWW, nie Django.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
