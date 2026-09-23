"""Rutas del módulo 2: calendario de vencimientos y alertas."""

from django.urls import path

from . import vistas

app_name = "calendario"

urlpatterns = [
    path("calendario/", vistas.CalendarioView.as_view(), name="calendario"),
    path("calendario/vencimientos/", vistas.ListaVencimientosView.as_view(), name="lista"),
    path(
        "calendario/vencimientos/nuevo/",
        vistas.CrearVencimientoView.as_view(),
        name="crear_vencimiento",
    ),
    path(
        "calendario/vencimientos/<int:pk>/",
        vistas.DetalleVencimientoView.as_view(),
        name="detalle",
    ),
    path(
        "calendario/vencimientos/<int:pk>/editar/",
        vistas.EditarVencimientoView.as_view(),
        name="editar_vencimiento",
    ),
    path(
        "calendario/vencimientos/<int:pk>/estado/",
        vistas.CambiarEstadoVencimientoView.as_view(),
        name="cambiar_estado",
    ),
    path(
        "calendario/vencimientos/<int:pk>/validar/",
        vistas.ValidarVencimientoView.as_view(),
        name="validar",
    ),
    path(
        "calendario/generar/",
        vistas.GenerarVencimientosView.as_view(),
        name="generar",
    ),
    path(
        "calendario/clientes/<int:pk_cliente>/calcular/",
        vistas.CalcularVencimientosClienteView.as_view(),
        name="calcular_cliente",
    ),
    # Tabla de referencia DIAN (solo Administrador)
    path("calendario/dian/", vistas.CargarDianView.as_view(), name="cargar_dian"),
    path(
        "calendario/dian/importar/",
        vistas.ImportarDianView.as_view(),
        name="importar_dian",
    ),
    path(
        "calendario/dian/plantilla/",
        vistas.DescargarPlantillaDianView.as_view(),
        name="plantilla_dian",
    ),
    # Alertas
    path(
        "calendario/vencimientos/<int:pk_vencimiento>/alertas/nueva/",
        vistas.CrearAlertaView.as_view(),
        name="crear_alerta",
    ),
    path(
        "calendario/alertas/<int:pk>/eliminar/",
        vistas.EliminarAlertaView.as_view(),
        name="eliminar_alerta",
    ),
    # Anotaciones
    path(
        "calendario/anotaciones/nueva/",
        vistas.CrearAnotacionView.as_view(),
        name="crear_anotacion",
    ),
    path(
        "calendario/anotaciones/<int:pk>/eliminar/",
        vistas.EliminarAnotacionView.as_view(),
        name="eliminar_anotacion",
    ),
]
