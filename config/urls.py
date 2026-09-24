"""Rutas principales del proyecto Contanika."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("aplicaciones.seguridad.urls")),
    path("", include("aplicaciones.clientes.urls")),
    path("", include("aplicaciones.calendario.urls")),
    path("", include("aplicaciones.tareas.urls")),
]
