from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as serve_static

# Główny router projektu — /admin/ to panel administracyjny Django,
# wszystko inne (na razie tylko "/") obsługuje aplikacja core (core/urls.py).
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]

# Serwowanie zdjęć wgranych przez admina (MEDIA_ROOT). Celowo NIE używamy
# tu django.conf.urls.static.static() — ta funkcja ma WEWNĄTRZ SIEBIE
# sprawdzenie "if not settings.DEBUG: return []", więc na produkcji
# (DEBUG=False) po prostu nie rejestruje żadnego URL-a dla /media/, mimo że
# nic na to nie wskazuje z zewnątrz (to właśnie był powód, dla którego
# zdjęcia dawały 404 mimo że fizycznie były na dysku). Wywołujemy więc
# bezpośrednio widok django.views.static.serve, który tego sprawdzenia nie
# ma. Normalnie serwowanie plików w ten sposób zostawia się osobnemu
# serwerowi WWW/CDN-owi (Django samo w sobie nie jest do tego
# zoptymalizowane) — ale na Render (darmowy plan) nie ma osobnego serwera
# WWW obok Django ani trwałego storage w chmurze, więc to jedyny sposób,
# żeby zdjęcia w ogóle działały. Świadomy kompromis na start — docelowo
# (patrz komentarz przy MEDIA_ROOT w settings.py) to powinno przenieść się
# na Cloudflare R2/S3.
urlpatterns += [
    re_path(
        r"^%s(?P<path>.*)$" % settings.MEDIA_URL.lstrip("/"),
        serve_static,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
