"""Rutas del asistente de consultas."""

from django.urls import path

from . import vistas

app_name = "asistente"
urlpatterns = [
    path("asistente/", vistas.AsistenteView.as_view(), name="inicio"),
    path("asistente/consultar/<slug:slug>/", vistas.ConsultarView.as_view(), name="consultar"),
]
