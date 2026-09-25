"""Rutas del módulo 5: hallazgos y revisiones contables."""

from django.urls import path

from . import vistas

app_name = "hallazgos"
urlpatterns = [
    path("hallazgos/", vistas.ListaHallazgosView.as_view(), name="lista"),
    path("hallazgos/nuevo/", vistas.CrearHallazgoView.as_view(), name="crear"),
    path("hallazgos/<int:pk>/", vistas.DetalleHallazgoView.as_view(), name="detalle"),
    path("hallazgos/<int:pk>/editar/", vistas.EditarHallazgoView.as_view(), name="editar"),
    path("hallazgos/<int:pk>/eliminar/", vistas.EliminarHallazgoView.as_view(), name="eliminar"),
    path("hallazgos/<int:pk>/estado/", vistas.CambiarEstadoHallazgoView.as_view(), name="cambiar_estado"),
    path(
        "hallazgos/<int:pk>/adjuntos/",
        vistas.AgregarAdjuntoHallazgoView.as_view(),
        name="agregar_adjunto",
    ),
    path(
        "hallazgos/adjuntos/<int:pk>/eliminar/",
        vistas.EliminarAdjuntoHallazgoView.as_view(),
        name="eliminar_adjunto",
    ),
    path(
        "hallazgos/adjuntos/<int:pk>/descargar/",
        vistas.DescargarAdjuntoHallazgoView.as_view(),
        name="descargar_adjunto",
    ),
]
