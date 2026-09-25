"""Rutas del módulo 4: expedición de documentos y certificados."""

from django.urls import path

from . import vistas

app_name = "documentos"

urlpatterns = [
    path("documentos/", vistas.HistoricoDocumentosView.as_view(), name="historico"),
    path("documentos/generar/", vistas.GenerarDocumentoView.as_view(), name="generar"),
    path("documentos/generar/campos/", vistas.CamposPlantillaParcialView.as_view(), name="campos_plantilla"),
    path("documentos/generar/confirmar/", vistas.ConfirmarDocumentoView.as_view(), name="confirmar"),
    path("documentos/mi-firma/", vistas.MiFirmaView.as_view(), name="mi_firma"),
    path("documentos/plantillas/", vistas.ListaPlantillasView.as_view(), name="plantillas"),
    path("documentos/plantillas/nueva/", vistas.CrearPlantillaView.as_view(), name="plantilla_crear"),
    path(
        "documentos/plantillas/<int:pk>/editar/",
        vistas.EditarPlantillaView.as_view(),
        name="plantilla_editar",
    ),
    path("documentos/<int:pk>/", vistas.DetalleDocumentoView.as_view(), name="detalle"),
    path("documentos/<int:pk>/descargar/", vistas.DescargarDocumentoView.as_view(), name="descargar"),
    path("documentos/<int:pk>/eliminar/", vistas.EliminarDocumentoView.as_view(), name="eliminar"),
]
