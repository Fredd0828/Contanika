"""Rutas del módulo 7: comunicaciones integradas."""

from django.urls import path

from . import vistas

app_name = "comunicaciones"
urlpatterns = [
    path("comunicaciones/", vistas.ListaComunicacionesView.as_view(), name="lista"),
    path("comunicaciones/registrar/", vistas.RegistrarComunicacionView.as_view(), name="registrar"),
    path(
        "comunicaciones/cliente/<int:pk_cliente>/",
        vistas.ComunicacionesClienteView.as_view(),
        name="cliente",
    ),
]
