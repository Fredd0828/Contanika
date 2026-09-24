"""Pruebas de los modelos del módulo 3: tablero de tareas Kanban."""

import pytest

from aplicaciones.tareas.models import HistorialTarea, Tarea

pytestmark = pytest.mark.django_db


@pytest.fixture
def tarea(cliente, usuario_junior):
    return Tarea.objects.create(
        cliente=cliente,
        titulo="Conciliar cartera de proveedores",
        responsable=usuario_junior,
        prioridad=Tarea.ALTA,
    )


def test_str_tarea(tarea):
    assert str(tarea) == "Conciliar cartera de proveedores (Por hacer)"


def test_cambiar_estado_crea_historial(tarea, usuario_administrador):
    historial = tarea.cambiar_estado(Tarea.EN_PROGRESO, usuario_administrador)
    tarea.refresh_from_db()

    assert tarea.estado == Tarea.EN_PROGRESO
    assert isinstance(historial, HistorialTarea)
    assert historial.estado_anterior == Tarea.POR_HACER
    assert historial.estado_nuevo == Tarea.EN_PROGRESO
    assert historial.usuario == usuario_administrador


def test_cambiar_estado_mismo_estado_no_crea_historial(tarea, usuario_administrador):
    resultado = tarea.cambiar_estado(Tarea.POR_HACER, usuario_administrador)
    assert resultado is None
    assert HistorialTarea.objects.count() == 0
