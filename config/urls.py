"""Rutas principales del proyecto Contanika."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("aplicaciones.seguridad.urls")),
    path("", include("aplicaciones.clientes.urls")),
    path("", include("aplicaciones.calendario.urls")),
    path("", include("aplicaciones.tareas.urls")),
    path("", include("aplicaciones.documentos.urls")),
    path("", include("aplicaciones.hallazgos.urls")),
    path("", include("aplicaciones.finanzas.urls")),
    path("", include("aplicaciones.expediente.urls")),
    path("", include("aplicaciones.comunicaciones.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
