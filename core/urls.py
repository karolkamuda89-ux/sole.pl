from django.urls import path

from . import views

app_name = "core"

# Kolejne podstrony (np. "kontakt/") będą dopisywane tutaj jako kolejne
# path(...), gdy ruszymy z resztą serwisu.
urlpatterns = [
    path("", views.home, name="home"),
    # <location> to "polska" albo "teneryfa" (patrz Property.LOCATION_CHOICES) —
    # jeden widok (oferta_lista) obsługuje obie strony listy ofert.
    path("oferta/<str:location>/", views.oferta_lista, name="oferta_lista"),
    path("oferta/<str:location>/<slug:slug>/", views.oferta_detail, name="oferta_detail"),
    path("polityka-prywatnosci/", views.polityka_prywatnosci, name="polityka_prywatnosci"),
]
