"""
Consultas reutilizables del módulo 3: tablero de tareas Kanban.

Se separan de las vistas para reutilizarse en el tablero, el detalle de la
tarea y el futuro reporte de tareas (Módulo 10).
"""

from datetime import date, timedelta

from django.utils import timezone

from .models import HistorialTarea, Tarea

# Ventana de días para calcular las notificaciones recientes. No existe una
# tabla de notificaciones en el diccionario de datos: se calculan a partir
# del historial de la tarea, sin marcar leído/no leído (decisión de sesión,
# Módulo 3 bloque 1).
DIAS_NOTIFICACIONES = 7

RANGO_PRIORIDAD = {Tarea.ALTA: 0, Tarea.MEDIA: 1, Tarea.BAJA: 2}


def tareas_visibles(usuario):
    """
    Tareas que el usuario puede ver según su rol.

    El Contador Junior solo ve las tareas asignadas a él; los demás roles
    ven el tablero completo del equipo.
    """
    consulta = Tarea.objects.select_related("cliente", "responsable")
    if usuario.es_contador_junior:
        consulta = consulta.filter(responsable=usuario)
    return consulta


def filtrar_tareas(usuario, cliente=None, responsable=None, prioridad=None, tipo_tarea=None):
    """Aplica los filtros desplegables del tablero; todos son opcionales."""
    consulta = tareas_visibles(usuario)
    if cliente:
        consulta = consulta.filter(cliente_id=cliente)
    if responsable:
        consulta = consulta.filter(responsable_id=responsable)
    if prioridad:
        consulta = consulta.filter(prioridad=prioridad)
    if tipo_tarea:
        consulta = consulta.filter(tipo_tarea=tipo_tarea)
    return consulta


def agrupar_por_estado(tareas):
    """
    Agrupa las tareas por columna del Kanban, ordenadas por prioridad
    (alta primero) y fecha de vencimiento más próxima.
    """
    columnas = {estado: [] for estado, _ in Tarea.OPCIONES_ESTADO}
    for tarea in sorted(
        tareas,
        key=lambda t: (
            RANGO_PRIORIDAD.get(t.prioridad, 99),
            t.fecha_vencimiento or date.max,
        ),
    ):
        columnas.setdefault(tarea.estado, []).append(tarea)
    return columnas


def opciones_filtro_tareas(usuario):
    """Tipos de tarea ya registrados, para sugerirlos en el filtro abierto."""
    tipos = (
        tareas_visibles(usuario)
        .exclude(tipo_tarea="")
        .values_list("tipo_tarea", flat=True)
        .distinct()
        .order_by("tipo_tarea")
    )
    return {"tipos_tarea": list(tipos)}


def notificaciones_usuario(usuario, limite=15):
    """
    Cambios de estado recientes en tareas asignadas al usuario, hechos por
    otra persona (RQF: notificación al responsable al cambiar de estado).
    """
    desde = timezone.now() - timedelta(days=DIAS_NOTIFICACIONES)
    return (
        HistorialTarea.objects.filter(tarea__responsable=usuario, fecha_cambio__gte=desde)
        .exclude(usuario=usuario)
        .select_related("tarea", "usuario", "tarea__cliente")
        .order_by("-fecha_cambio")[:limite]
    )
