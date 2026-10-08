"""Rutas del módulo 3: tablero de tareas Kanban."""

from django.urls import path

from . import vistas

app_name = "tareas"

urlpatterns = [
    path("tareas/", vistas.TableroTareasView.as_view(), name="tablero"),
    path("tareas/nueva/", vistas.CrearTareaView.as_view(), name="crear"),
    path("tareas/<int:pk>/", vistas.DetalleTareaView.as_view(), name="detalle"),
    path("tareas/<int:pk>/editar/", vistas.EditarTareaView.as_view(), name="editar"),
    path("tareas/<int:pk>/eliminar/", vistas.EliminarTareaView.as_view(), name="eliminar"),
    path("tareas/<int:pk>/estado/", vistas.CambiarEstadoTareaView.as_view(), name="cambiar_estado"),
    path(
        "tareas/<int:pk>/observaciones/",
        vistas.AgregarObservacionView.as_view(),
        name="agregar_observacion",
    ),
    path("tareas/notificaciones/", vistas.NotificacionesTareaView.as_view(), name="notificaciones"),
]
