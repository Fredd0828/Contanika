"""Rutas del módulo 9: expediente y bitácora por cliente."""

from django.urls import path

from . import vistas

app_name = "expediente"
urlpatterns = [
    path("expediente/", vistas.ListaAnotacionesView.as_view(), name="lista"),
    path("expediente/nueva/", vistas.CrearAnotacionView.as_view(), name="crear"),
    path("expediente/cliente/<int:pk_cliente>/", vistas.ExpedienteClienteView.as_view(), name="cliente"),
    path("expediente/<int:pk>/archivar/", vistas.ArchivarAnotacionView.as_view(), name="archivar"),
    path(
        "expediente/<int:pk>/restaurar/",
        vistas.ArchivarAnotacionView.as_view(restaurar=True),
        name="restaurar",
    ),
    path(
        "expediente/adjuntos/<int:pk>/descargar/",
        vistas.DescargarAdjuntoAnotacionView.as_view(),
        name="descargar_adjunto",
    ),
]
