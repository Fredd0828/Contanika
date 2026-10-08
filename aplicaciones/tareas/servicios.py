"""
Reglas de negocio del módulo 3: tablero de tareas Kanban.

Las vistas delegan en estas funciones la escritura en los modelos, incluida
la sincronización con el vencimiento del calendario cuando la tarea se marca
para mostrarse allí (integración Módulo 2 ↔ Módulo 3).
"""

from django.core.exceptions import PermissionDenied
from django.db import transaction

from aplicaciones.calendario.models import Vencimiento

from .models import ObservacionTarea, Tarea


@transaction.atomic
def crear_tarea(formulario):
    """Crea una tarea nueva (siempre inicia en 'Por hacer') y sincroniza el calendario."""
    tarea = formulario.save()
    sincronizar_vencimiento(tarea)
    return tarea


@transaction.atomic
def actualizar_tarea(tarea, formulario):
    """Edita una tarea existente y sincroniza el calendario."""
    tarea = formulario.save()
    sincronizar_vencimiento(tarea)
    return tarea


@transaction.atomic
def eliminar_tarea(tarea):
    """Elimina la tarea y el vencimiento que hubiera generado en el calendario."""
    Vencimiento.objects.filter(tarea=tarea).delete()
    tarea.delete()
    return True


@transaction.atomic
def cambiar_estado_tarea(tarea, nuevo_estado, usuario):
    """
    Cambia el estado de la tarea y sincroniza el vencimiento del calendario.

    El Contador Junior solo puede cambiar el estado de las tareas que tiene
    asignadas; Administrador y Contador Senior pueden cambiar cualquiera.
    """
    if usuario.es_contador_junior and tarea.responsable_id != usuario.id_usuario:
        raise PermissionDenied("Solo puede actualizar el estado de sus propias tareas.")
    historial = tarea.cambiar_estado(nuevo_estado, usuario)
    sincronizar_vencimiento(tarea)
    return historial


@transaction.atomic
def agregar_observacion(tarea, usuario, contenido):
    """Registra una observación de avance sobre la tarea."""
    return ObservacionTarea.objects.create(tarea=tarea, usuario=usuario, contenido=contenido)


def sincronizar_vencimiento(tarea):
    """
    Refleja la tarea en el calendario cuando `mostrar_en_calendario` está
    activo, con la misma fecha, cliente y responsable de la tarea.

    Si se desactiva la casilla o la tarea no tiene fecha de vencimiento, se
    elimina el vencimiento generado (si existía). El estado de presentación
    del vencimiento sigue el estado de la tarea: 'Terminado' se refleja como
    'Presentada'; cualquier otro estado, como 'Pendiente'.
    """
    if tarea.mostrar_en_calendario and tarea.fecha_vencimiento:
        Vencimiento.objects.update_or_create(
            tarea=tarea,
            defaults={
                "cliente": tarea.cliente,
                "tipo_obligacion": tarea.titulo,
                "fecha_vencimiento": tarea.fecha_vencimiento,
                "responsable": tarea.responsable,
                "estado_presentacion": (
                    Vencimiento.PRESENTADA if tarea.estado == Tarea.TERMINADO else Vencimiento.PENDIENTE
                ),
            },
        )
    else:
        Vencimiento.objects.filter(tarea=tarea).delete()
