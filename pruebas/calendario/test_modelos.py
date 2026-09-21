"""Pruebas de los modelos del módulo 2: vencimientos y alertas."""

from datetime import date, timedelta

import pytest

from aplicaciones.calendario.models import ConfiguracionAlerta, Vencimiento
from aplicaciones.tareas.models import Tarea

pytestmark = pytest.mark.django_db


def test_vencimiento_nacional_es_automatico(cliente, usuario_administrador):
    """Un vencimiento nacional sin tarea asociada es automático de la DIAN."""
    vencimiento = Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="IVA",
        ambito=Vencimiento.NACIONAL,
        fecha_vencimiento=date.today() + timedelta(days=10),
        responsable=usuario_administrador,
        estado_validacion=Vencimiento.PENDIENTE_VALIDAR,
    )
    assert vencimiento.es_automatico_dian is True


def test_vencimiento_de_tarea_no_es_automatico(cliente, usuario_administrador):
    """Un vencimiento originado en una tarea marcada no es automático DIAN."""
    tarea = Tarea.objects.create(
        cliente=cliente,
        titulo="Preparar conciliación bancaria",
        responsable=usuario_administrador,
        fecha_vencimiento=date.today() + timedelta(days=5),
        mostrar_en_calendario=True,
    )
    vencimiento = Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="Tarea del tablero",
        ambito=Vencimiento.MUNICIPAL,
        fecha_vencimiento=tarea.fecha_vencimiento,
        tarea=tarea,
    )
    assert vencimiento.es_automatico_dian is False


def test_alerta_configurada_con_anticipacion_y_canal(cliente):
    """Cada vencimiento puede tener alertas con anticipación y canal propios."""
    vencimiento = Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="Retención en la fuente",
        ambito=Vencimiento.NACIONAL,
        fecha_vencimiento=date.today() + timedelta(days=20),
    )
    alerta = ConfiguracionAlerta.objects.create(
        vencimiento=vencimiento,
        dias_anticipacion=5,
        canal=ConfiguracionAlerta.CORREO,
    )
    assert alerta.dias_anticipacion == 5
    assert vencimiento.alertas.count() == 1
