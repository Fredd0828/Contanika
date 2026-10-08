"""Rutas del módulo 1: gestión de clientes."""

from django.urls import path

from . import vistas

app_name = "clientes"

urlpatterns = [
    path("clientes/", vistas.ListaClientesView.as_view(), name="lista"),
    path("clientes/nuevo/", vistas.CrearClienteView.as_view(), name="crear"),
    path("clientes/importar/", vistas.ImportarClientesView.as_view(), name="importar"),
    path("clientes/plantilla/", vistas.DescargarPlantillaClientesView.as_view(), name="plantilla"),
    path(
        "clientes/credenciales/reporte/",
        vistas.ReporteCredencialesTodosView.as_view(),
        name="reporte_credenciales_todos",
    ),
    path("clientes/<int:pk>/", vistas.DetalleClienteView.as_view(), name="detalle"),
    path("clientes/<int:pk>/editar/", vistas.EditarClienteView.as_view(), name="editar"),
    path("clientes/<int:pk>/inactivar/", vistas.InactivarClienteView.as_view(), name="inactivar"),
    # Credenciales
    path(
        "clientes/<int:pk_cliente>/credenciales/nueva/",
        vistas.CredencialCrearView.as_view(),
        name="credencial_crear",
    ),
    path(
        "clientes/<int:pk_cliente>/credenciales/<int:pk>/editar/",
        vistas.CredencialEditarView.as_view(),
        name="credencial_editar",
    ),
    path(
        "clientes/<int:pk_cliente>/credenciales/<int:pk>/eliminar/",
        vistas.CredencialEliminarView.as_view(),
        name="credencial_eliminar",
    ),
    path(
        "clientes/<int:pk_cliente>/credenciales/reporte/",
        vistas.ReporteCredencialesView.as_view(),
        name="reporte_credenciales",
    ),
]
