"""
Django settings for config project.
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# Ustawienia "wrażliwe" (SECRET_KEY, DEBUG) — czytane ze zmiennych
# środowiskowych, z bezpiecznymi wartościami domyślnymi do pracy lokalnej.
# Na Render (i każdym prawdziwym hostingu) trzeba je ustawić jawnie w
# panelu: DJANGO_SECRET_KEY na losowy ciąg znaków, DJANGO_DEBUG=False.
# Lokalnie nic nie trzeba robić — działa tak jak dotychczas.
# --------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-change-me-before-deploying"
)

DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

# Kropka na początku = dowolna subdomena. ".onrender.com" to Render,
# ".ngrok-*" zostają na wypadek kolejnego szybkiego podglądu przez tunel.
# Jeśli/jak dojdzie własna domena, dopisz ją tutaj (albo ustaw przez
# zmienną środowiskową DJANGO_ALLOWED_HOSTS, oddzieloną przecinkami).
ALLOWED_HOSTS = [
    "localhost", "127.0.0.1", ".onrender.com",
    ".ngrok-free.app", ".ngrok-free.dev", ".ngrok.io", ".ngrok.dev",
] + [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h]

# Render (jak ngrok) sam obsługuje HTTPS, ale do Django przekazuje ruch
# już jako zwykłe HTTP — bez poniższego Django "nie wie", że połączenie
# było szyfrowane, i odrzuca np. logowanie do admina jako podejrzane
# (CSRF/"Forbidden") — to ten sam mechanizm, który naprawiał błąd
# "dostęp zablokowany" przy testach przez ngrok.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
    "https://*.ngrok-free.app", "https://*.ngrok-free.dev",
    "https://*.ngrok.io", "https://*.ngrok.dev",
]

# Wymuszaj HTTPS/bezpieczne ciasteczka tylko na produkcji (DEBUG=False) —
# lokalnie (zwykłe http://localhost:8000) te ustawienia by tylko przeszkadzały.
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",  # nasza aplikacja ze stroną główną
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # whitenoise serwuje pliki statyczne (core/static/, po `collectstatic`)
    # bezpośrednio z Django — bez tego, na Render nic by nie było CSS/JS,
    # bo tam nie ma osobnego Nginksa, który normalnie by się tym zajął.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.meta_pixel",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Lokalnie (brak zmiennej DATABASE_URL) — dalej zwykłe SQLite, jak dotąd.
# Na Render Postgres podłącza się automatycznie: dodanie tam bazy Postgres
# do web service ustawia DATABASE_URL samo, nic nie trzeba kopiować ręcznie.
# WAŻNE: SQLite NIE nadaje się na Render (dysk tam jest efemeryczny — plik
# bazy znika przy każdym redeployu), więc na produkcji zawsze musi być
# ustawione DATABASE_URL wskazujące na prawdziwy Postgres.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "pl"

TIME_ZONE = "Europe/Warsaw"

USE_I18N = True

USE_TZ = True


STATIC_URL = "static/"

# CSS/JS/obrazki aplikacji "core" (core/static/core/...) Django znajduje
# automatycznie. Ten folder to dodatkowe, globalne pliki statyczne poza
# aplikacjami (np. favicon) — na razie pusty.
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# `python manage.py collectstatic` (uruchamiane przy każdym deployu na
# Render, patrz render.yaml) kopiuje WSZYSTKIE pliki statyczne właśnie
# tutaj — stąd whitenoise (MIDDLEWARE wyżej) je potem serwuje. Lokalnie
# ten folder zwykle nie istnieje i nie jest potrzebny — `runserver` czyta
# statyki bezpośrednio z core/static/, collectstatic nie jest wymagane.
STATIC_ROOT = BASE_DIR / "staticfiles"

# CompressedManifestStaticFilesStorage = whitenoise dorzuca do nazw plików
# hash treści (np. style.abcd1234.css) i nagłówki cache na rok — przeglądarka
# nie musi za każdym razem pobierać CSS/JS na nowo, a i tak dostanie świeżą
# wersję po każdej zmianie (bo hash w nazwie się zmieni).
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Pliki wgrywane przez admina (zdjęcia ofert) — inne niż STATIC: te trafiają
# tu przez formularze w panelu, a nie są częścią kodu strony. media/ jest
# w .gitignore (jak db.sqlite3) — obraz startowy odtwarza je z core/static/
# przez `python manage.py import_apartments`.
#
# UWAGA na Render (darmowy plan): dysk jest efemeryczny, więc nowe zdjęcia
# wgrane przez panel PO wdrożeniu znikną przy kolejnym redeployu. Zdjęcia
# 7 apartamentów wgrane na starcie (przez import_apartments w czasie builda)
# przetrwają do następnego deployu, ale nie dłużej. Docelowe rozwiązanie to
# przeniesienie MEDIA na zewnętrzny storage (np. Cloudflare R2 / S3) —
# osobny temat na później, gdy strona realnie zacznie żyć.
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==========================================================================
# E-mail — wysyłka powiadomień o nowych wiadomościach z formularza kontaktowego.
#
# Domyślnie (bez zmiennych środowiskowych) działa EMAIL_BACKEND "console" —
# zamiast realnie wysyłać e-mail, wypisuje jego treść w terminalu, w którym
# działa `runserver`. To celowe: nie mamy tu prawdziwych danych logowania do
# skrzynki, a taki tryb pozwala przetestować cały mechanizm (zapis do bazy +
# próba wysyłki) bez ryzyka błędu przez brakujące/błędne hasło SMTP.
#
# Żeby realnie wysyłać na sole@sole.pl, trzeba przed uruchomieniem serwera
# ustawić w środowisku prawdziwe dane skrzynki nadawczej (np. w pliku .env
# lub zmiennych systemowych — NIGDY nie wpisuj hasła bezpośrednio w tym
# pliku, bo trafiłoby do gita):
#   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
#   EMAIL_HOST=smtp.twojhosting.pl
#   EMAIL_PORT=587
#   EMAIL_HOST_USER=twoj-adres@domena.pl
#   EMAIL_HOST_PASSWORD=haslo-lub-app-password
#   EMAIL_USE_TLS=True
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@sole.pl")

# Adres, na który trafiają powiadomienia o nowych wiadomościach z formularza.
CONTACT_EMAIL = "sole@sole.pl"


# ==========================================================================
# Meta Pixel (Facebook) — puste, dopóki nie wpiszesz tu prawdziwego ID
# z Meta Business Suite / Events Manager. Skrypt (core/static/core/js/
# cookie-consent.js, ładowany przez base.html) ładuje Pixel TYLKO gdy:
#   1) to ID jest ustawione, ORAZ
#   2) użytkownik kliknął "Akceptuję" w bannerze cookies na stronie.
# Zgodnie z core/templates/core/polityka-prywatnosci.html (sekcja 11) —
# jak wpiszesz prawdziwe ID, zaktualizuj też tamten opis, żeby był zgodny
# z rzeczywistością (mechanizm jest już gotowy, więc to tylko zmiana tekstu).
META_PIXEL_ID = os.environ.get("META_PIXEL_ID", "")
