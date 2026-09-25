"""Pruebas del modelo del módulo 5: hallazgos y revisiones contables."""

from datetime import date

import pytest

from aplicaciones.hallazgos.models import Hallazgo

pytestmark = pytest.mark.django_db


@pytest.fixture
def hallazgo(cliente):
    return Hallazgo.objects.create(
        cliente=cliente,
        tipo_hallazgo="Inconsistencia",
        fecha_inicio_periodo=date(2026, 1, 1),
        fecha_fin_periodo=date(2026, 1, 31),
        descripcion="Diferencia entre el libro auxiliar y el extracto bancario.",
    )


def test_str_incluye_tipo_cliente_y_estado(hallazgo):
    texto = str(hallazgo)
    assert hallazgo.tipo_hallazgo in texto
    assert hallazgo.cliente.nombre_razon_social in texto
    assert hallazgo.estado in texto


def test_cerrar_fija_estado_y_observacion(hallazgo):
    hallazgo.cerrar("Se conciliaron las partidas pendientes.")
    hallazgo.refresh_from_db()
    assert hallazgo.estado == Hallazgo.CERRADO
    assert hallazgo.observacion_cierre == "Se conciliaron las partidas pendientes."
