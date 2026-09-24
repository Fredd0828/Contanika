"""Pruebas de las consultas del módulo 3: visibilidad, filtros y notificaciones."""

from datetime import timedelta

import pytest
from django.utils import timezone

from aplicaciones.tareas.models import HistorialTarea, Tarea
from aplicaciones.tareas.selectores import (
    agrupar_por_estado,
    filtrar_tareas,
    notificaciones_usuario,
    opciones_filtro_tareas,
    tareas_visibles,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def tarea_admin(cliente, usuario_administrador):
    return Tarea.objects.create(
        cliente=cliente,
        titulo="Preparar retención",
        tipo_tarea="Declaración",
        responsable=usuario_administrador,
        prioridad=Tarea.MEDIA,
    )


@pytest.fixture
def tarea_junior(cliente_junior, usuario_junior):
    return Tarea.objects.create(
        cliente=cliente_junior,
        titulo="Reunir soportes",
        responsable=usuario_junior,
        prioridad=Tarea.ALTA,
    )


# ---------------------------------------------------------------------------
# tareas_visibles / filtrar_tareas
# ---------------------------------------------------------------------------


def test_junior_solo_ve_sus_tareas(usuario_junior, tarea_admin, tarea_junior):
    visibles = list(tareas_visibles(usuario_junior))
    assert visibles == [tarea_junior]


def test_admin_ve_todas_las_tareas(usuario_administrador, tarea_admin, tarea_junior):
    visibles = set(tareas_visibles(usuario_administrador))
    assert visibles == {tarea_admin, tarea_junior}


def test_filtrar_tareas_por_prioridad(usuario_administrador, tarea_admin, tarea_junior):
    resultado = list(filtrar_tareas(usuario_administrador, prioridad=Tarea.ALTA))
    assert resultado == [tarea_junior]


def test_filtrar_tareas_por_tipo(usuario_administrador, tarea_admin, tarea_junior):
    resultado = list(filtrar_tareas(usuario_administrador, tipo_tarea="Declaración"))
    assert resultado == [tarea_admin]


# ---------------------------------------------------------------------------
# agrupar_por_estado
# ---------------------------------------------------------------------------


def test_agrupar_por_estado_todas_las_columnas_existen(usuario_administrador):
    columnas = agrupar_por_estado(tareas_visibles(usuario_administrador))
    assert set(columnas.keys()) == {estado for estado, _ in Tarea.OPCIONES_ESTADO}


def test_agrupar_por_estado_ordena_por_prioridad(usuario_administrador, tarea_admin, tarea_junior):
    """La prioridad alta queda antes que la media dentro de la misma columna."""
    columnas = agrupar_por_estado(tareas_visibles(usuario_administrador))
    assert columnas[Tarea.POR_HACER] == [tarea_junior, tarea_admin]


# ---------------------------------------------------------------------------
# opciones_filtro_tareas
# ---------------------------------------------------------------------------


def test_opciones_filtro_tareas_lista_tipos_registrados(usuario_administrador, tarea_admin, tarea_junior):
    opciones = opciones_filtro_tareas(usuario_administrador)
    assert opciones["tipos_tarea"] == ["Declaración"]


# ---------------------------------------------------------------------------
# notificaciones_usuario
# ---------------------------------------------------------------------------


def test_notificaciones_usuario_excluye_cambios_propios(tarea_junior, usuario_junior):
    """El propio responsable no se notifica a sí mismo de sus cambios."""
    tarea_junior.cambiar_estado(Tarea.EN_PROGRESO, usuario_junior)
    assert list(notificaciones_usuario(usuario_junior)) == []


def test_notificaciones_usuario_incluye_cambios_de_otros(tarea_junior, usuario_junior, usuario_administrador):
    historial = tarea_junior.cambiar_estado(Tarea.EN_PROGRESO, usuario_administrador)
    notificaciones = list(notificaciones_usuario(usuario_junior))
    assert notificaciones == [historial]


def test_notificaciones_usuario_ignora_cambios_antiguos(tarea_junior, usuario_junior, usuario_administrador):
    """Los cambios fuera de la ventana de días no se muestran como notificación."""
    historial = tarea_junior.cambiar_estado(Tarea.EN_PROGRESO, usuario_administrador)
    HistorialTarea.objects.filter(pk=historial.pk).update(fecha_cambio=timezone.now() - timedelta(days=30))
    assert list(notificaciones_usuario(usuario_junior)) == []
