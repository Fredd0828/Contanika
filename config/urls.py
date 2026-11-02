"""Rutas principales del proyecto Contanika."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from aplicaciones.comunes.vistas import MediaProtegidaView, RobotsView, SaludView, VersionView

urlpatterns = [
    path(settings.RUTA_ADMIN, admin.site.urls),
    path("robots.txt", RobotsView.as_view(), name="robots"),
    path("salud/", SaludView.as_view(), name="salud"),
    path("version/", VersionView.as_view(), name="version"),
    # Los archivos subidos no se publican como estáticos: pasan por una vista
    # que exige sesión y solo entrega las imágenes que le corresponden al usuario.
    path(f"{settings.MEDIA_URL.lstrip('/')}<path:ruta>", MediaProtegidaView.as_view(), name="media"),
    path("", include("aplicaciones.seguridad.urls")),
    path("", include("aplicaciones.clientes.urls")),
    path("", include("aplicaciones.calendario.urls")),
    path("", include("aplicaciones.tareas.urls")),
    path("", include("aplicaciones.documentos.urls")),
    path("", include("aplicaciones.hallazgos.urls")),
    path("", include("aplicaciones.finanzas.urls")),
    path("", include("aplicaciones.expediente.urls")),
    path("", include("aplicaciones.comunicaciones.urls")),
    path("", include("aplicaciones.reportes.urls")),
]
