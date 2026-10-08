"""Pruebas de las reglas de negocio del módulo 3, incluida la sincronización con el Calendario."""

from datetime import date

import pytest
from django.core.exceptions import PermissionDenied

from aplicaciones.calendario.models import Vencimiento
from aplicaciones.tareas.formularios import TareaForm
from aplicaciones.tareas.models import ObservacionTarea, Tarea
from aplicaciones.tareas.servicios import (
    actualizar_tarea,
    agregar_observacion,
    cambiar_estado_tarea,
    crear_tarea,
    eliminar_tarea,
    sincronizar_vencimiento,
)

pytestmark = pytest.mark.django_db


def _formulario_valido(cliente, usuario, **overrides):
    datos = {
        "cliente": cliente.pk,
        "titulo": "Preparar exógena formato 1001",
        "tipo_tarea": "Exógena",
        "prioridad": Tarea.MEDIA,
    }
    datos.update(overrides)
    formulario = TareaForm(datos, usuario=usuario)
    assert formulario.is_valid(), formulario.errors
    return formulario


@pytest.fixture
def tarea(cliente, usuario_administrador):
    return Tarea.objects.create(
        cliente=cliente,
        titulo="Conciliar cartera",
        responsable=usuario_administrador,
        prioridad=Tarea.MEDIA,
    )


# ---------------------------------------------------------------------------
# crear_tarea / actualizar_tarea
# ---------------------------------------------------------------------------


def test_crear_tarea_inicia_en_por_hacer(cliente, usuario_administrador):
    formulario = _formulario_valido(cliente, usuario_administrador)
    tarea = crear_tarea(formulario)
    assert tarea.estado == Tarea.POR_HACER
    assert tarea.pk is not None


def test_crear_tarea_sin_mostrar_en_calendario_no_genera_vencimiento(cliente, usuario_administrador):
    formulario = _formulario_valido(cliente, usuario_administrador)
    crear_tarea(formulario)
    assert Vencimiento.objects.count() == 0


def test_crear_tarea_con_mostrar_en_calendario_genera_vencimiento(cliente, usuario_administrador):
    formulario = _formulario_valido(
        cliente,
        usuario_administrador,
        mostrar_en_calendario=True,
        fecha_vencimiento="2026-05-20",
    )
    tarea = crear_tarea(formulario)

    vencimiento = Vencimiento.objects.get(tarea=tarea)
    assert vencimiento.cliente == cliente
    assert vencimiento.tipo_obligacion == tarea.titulo
    assert vencimiento.fecha_vencimiento == date(2026, 5, 20)
    assert vencimiento.estado_presentacion == Vencimiento.PENDIENTE


def test_actualizar_tarea_desactivar_mostrar_elimina_vencimiento(tarea, usuario_administrador):
    tarea.mostrar_en_calendario = True
    tarea.fecha_vencimiento = date(2026, 5, 20)
    tarea.save()
    sincronizar_vencimiento(tarea)
    assert Vencimiento.objects.filter(tarea=tarea).exists()

    formulario = TareaForm(
        {
            "cliente": tarea.cliente_id,
            "titulo": tarea.titulo,
            "prioridad": tarea.prioridad,
            "fecha_vencimiento": "2026-05-20",
            "mostrar_en_calendario": False,
        },
        instance=tarea,
        usuario=usuario_administrador,
    )
    assert formulario.is_valid(), formulario.errors
    actualizar_tarea(tarea, formulario)
    assert not Vencimiento.objects.filter(tarea=tarea).exists()


def test_eliminar_tarea_elimina_vencimiento_asociado(tarea):
    tarea.mostrar_en_calendario = True
    tarea.fecha_vencimiento = date(2026, 5, 20)
    tarea.save()
    sincronizar_vencimiento(tarea)
    assert Vencimiento.objects.filter(tarea=tarea).exists()

    eliminar_tarea(tarea)
    assert Vencimiento.objects.count() == 0
    assert not Tarea.objects.filter(pk=tarea.pk).exists()


# ---------------------------------------------------------------------------
# cambiar_estado_tarea
# ---------------------------------------------------------------------------


def test_cambiar_estado_admin_cualquier_tarea(tarea, usuario_administrador):
    historial = cambiar_estado_tarea(tarea, Tarea.EN_PROGRESO, usuario_administrador)
    tarea.refresh_from_db()
    assert tarea.estado == Tarea.EN_PROGRESO
    assert historial.estado_nuevo == Tarea.EN_PROGRESO


def test_cambiar_estado_junior_solo_su_propia_tarea(cliente_junior, usuario_junior):
    tarea = Tarea.objects.create(cliente=cliente_junior, titulo="Reunir soportes", responsable=usuario_junior)
    cambiar_estado_tarea(tarea, Tarea.EN_PROGRESO, usuario_junior)
    tarea.refresh_from_db()
    assert tarea.estado == Tarea.EN_PROGRESO


def test_cambiar_estado_junior_tarea_ajena_lanza_permission_denied(tarea, usuario_junior):
    """El Contador Junior no puede cambiar el estado de tareas de otro responsable."""
    with pytest.raises(PermissionDenied):
        cambiar_estado_tarea(tarea, Tarea.EN_PROGRESO, usuario_junior)


def test_cambiar_estado_terminado_marca_vencimiento_presentada(tarea, usuario_administrador):
    tarea.mostrar_en_calendario = True
    tarea.fecha_vencimiento = date(2026, 5, 20)
    tarea.save()
    sincronizar_vencimiento(tarea)

    cambiar_estado_tarea(tarea, Tarea.TERMINADO, usuario_administrador)
    vencimiento = Vencimiento.objects.get(tarea=tarea)
    assert vencimiento.estado_presentacion == Vencimiento.PRESENTADA


# ---------------------------------------------------------------------------
# agregar_observacion
# ---------------------------------------------------------------------------


def test_agregar_observacion_crea_registro(tarea, usuario_administrador):
    observacion = agregar_observacion(tarea, usuario_administrador, "Se solicitaron soportes al cliente.")
    assert isinstance(observacion, ObservacionTarea)
    assert observacion.tarea == tarea
    assert observacion.usuario == usuario_administrador
