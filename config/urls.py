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

# Serwowanie zdjęć wgranych przez admina (MEDIA_ROOT). Normalnie robi się
# to tylko w DEBUG i na produkcji zostawia serwerowi WWW/CDN-owi (Django
# samo w sobie nie jest do tego zoptymalizowane) — ale na Render (darmowy
# plan) nie ma osobnego serwera WWW obok Django ani trwałego dysku pod
# storage w chmurze, więc to jedyny sposób, żeby zdjęcia w ogóle działały.
# Świadomy kompromis na start — docelowo (patrz komentarz przy MEDIA_ROOT
# w settings.py) to powinno przenieść się na Cloudflare R2/S3.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
