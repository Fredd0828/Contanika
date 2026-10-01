"""Fixtures del módulo 10: reportes y análisis (reutiliza las de finanzas)."""

from datetime import date
from decimal import Decimal

import pytest

from aplicaciones.calendario.models import Vencimiento
from aplicaciones.finanzas import servicios as servicios_finanzas
from aplicaciones.tareas.models import Tarea
from pruebas.finanzas import conftest as fixtures_finanzas

# Fixtures del módulo 6 reutilizadas aquí (cuentas de cobro con PDF y abonos).
despacho = fixtures_finanzas.despacho
generar_cuenta = fixtures_finanzas.generar_cuenta
media_root_temporal = fixtures_finanzas.media_root_temporal
metodo_transferencia = fixtures_finanzas.metodo_transferencia


@pytest.fixture
def datos_reportes(
    generar_cuenta, metodo_transferencia, cliente, cliente_junior, usuario_administrador, usuario_junior
):
    """Un escenario pequeño con datos de todos los reportes para dos clientes."""
    cuenta = generar_cuenta(cliente, valor_total=Decimal("1000000"), fecha_vencimiento_pago=date(2026, 8, 10))
    servicios_finanzas.registrar_abono(
        cuenta,
        fecha=date(2026, 9, 5),
        monto=Decimal("400000"),
        metodo_pago=metodo_transferencia,
        usuario=usuario_administrador,
    )
    cuenta_junior = generar_cuenta(cliente_junior, valor_total=Decimal("500000"))
    Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="IVA bimestral",
        fecha_vencimiento=date(2026, 3, 17),
        responsable=usuario_administrador,
    )
    Vencimiento.objects.create(
        cliente=cliente_junior,
        tipo_obligacion="Retención en la fuente",
        fecha_vencimiento=date(2026, 12, 10),
        responsable=usuario_junior,
    )
    Tarea.objects.create(
        cliente=cliente,
        titulo="Conciliar bancos",
        responsable=usuario_administrador,
        fecha_vencimiento=date(2026, 1, 5),
    )
    Tarea.objects.create(
        cliente=cliente_junior, titulo="Archivar soportes", responsable=usuario_junior, estado=Tarea.TERMINADO
    )
    return {"cuenta": cuenta, "cuenta_junior": cuenta_junior}
