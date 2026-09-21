"""Rutas de autenticación y panel principal del sistema."""

from django.urls import path

from . import vistas

app_name = "seguridad"

urlpatterns = [
    path("", vistas.PanelView.as_view(), name="panel"),
    path("iniciar-sesion/", vistas.IniciarSesionView.as_view(), name="iniciar_sesion"),
    path("cerrar-sesion/", vistas.CerrarSesionView.as_view(), name="cerrar_sesion"),
]
