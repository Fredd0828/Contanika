"""Pruebas de los formularios del módulo 3: tablero de tareas Kanban."""

import pytest

from aplicaciones.tareas.formularios import (
    CambiarEstadoTareaForm,
    FiltroTareasForm,
    ObservacionTareaForm,
    TareaForm,
)
from aplicaciones.tareas.models import Tarea

pytestmark = pytest.mark.django_db


def test_tarea_form_valido_minimo(cliente, usuario_administrador):
    formulario = TareaForm(
        {"cliente": cliente.pk, "titulo": "Declarar IVA", "prioridad": Tarea.MEDIA},
        usuario=usuario_administrador,
    )
    assert formulario.is_valid(), formulario.errors


def test_tarea_form_exige_fecha_si_mostrar_en_calendario(cliente, usuario_administrador):
    formulario = TareaForm(
        {
            "cliente": cliente.pk,
            "titulo": "Declarar IVA",
            "prioridad": Tarea.MEDIA,
            "mostrar_en_calendario": True,
        },
        usuario=usuario_administrador,
    )
    assert not formulario.is_valid()
    assert "fecha_vencimiento" in formulario.errors


def test_tarea_form_junior_solo_ve_sus_clientes(cliente, cliente_junior, usuario_junior):
    formulario = TareaForm(usuario=usuario_junior)
    clientes = list(formulario.fields["cliente"].queryset)
    assert clientes == [cliente_junior]


def test_cambiar_estado_tarea_form_valida_opciones(cliente):
    formulario = CambiarEstadoTareaForm({"estado": Tarea.EN_REVISION})
    assert formulario.is_valid()

    formulario_invalido = CambiarEstadoTareaForm({"estado": "Inventado"})
    assert not formulario_invalido.is_valid()


def test_observacion_tarea_form_requiere_contenido():
    assert not ObservacionTareaForm({"contenido": ""}).is_valid()
    assert ObservacionTareaForm({"contenido": "Se avanzó con el cliente."}).is_valid()


def test_filtro_tareas_form_tipos_desde_opciones(usuario_administrador):
    formulario = FiltroTareasForm(
        usuario=usuario_administrador,
        opciones={"tipos_tarea": ["Declaración", "Conciliación"]},
    )
    valores = [valor for valor, _ in formulario.fields["tipo_tarea"].choices]
    assert valores == ["", "Declaración", "Conciliación"]
