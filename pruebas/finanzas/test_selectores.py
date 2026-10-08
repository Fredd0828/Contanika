"""Pruebas de los selectores del módulo 6: honorarios, catálogos y cuentas de cobro."""

from datetime import date
from decimal import Decimal

import pytest
from django.utils import timezone

from aplicaciones.finanzas import selectores, servicios
from aplicaciones.finanzas.models import CuentaCobro, Honorario
from aplicaciones.finanzas.templatetags.finanzas_tags import formato_pesos

pytestmark = pytest.mark.django_db


def test_administrador_ve_todas_las_cuentas(usuario_administrador, cuenta_cliente, cuenta_cliente_junior):
    assert set(selectores.cuentas_cobro_visibles(usuario_administrador)) == {
        cuenta_cliente,
        cuenta_cliente_junior,
    }


def test_junior_solo_ve_cuentas_de_sus_clientes(usuario_junior, cuenta_cliente, cuenta_cliente_junior):
    assert list(selectores.cuentas_cobro_visibles(usuario_junior)) == [cuenta_cliente_junior]


def test_senior_sin_clientes_asignados_no_ve_cuentas(usuario_senior, cuenta_cliente):
    assert not selectores.cuentas_cobro_visibles(usuario_senior).exists()


def test_filtrar_cuentas_por_cliente_estado_periodo_y_fecha(
    usuario_administrador, cliente, cliente_junior, generar_cuenta
):
    mensual = generar_cuenta(cliente)
    anual = generar_cuenta(cliente_junior, periodo_facturado=CuentaCobro.ANUAL)
    CuentaCobro.objects.filter(pk=anual.pk).update(estado_pago=CuentaCobro.PAGADA)

    assert list(selectores.filtrar_cuentas_cobro(usuario_administrador, cliente=cliente)) == [mensual]
    assert list(selectores.filtrar_cuentas_cobro(usuario_administrador, estado_pago=CuentaCobro.PAGADA)) == [
        anual
    ]
    assert list(selectores.filtrar_cuentas_cobro(usuario_administrador, periodo=CuentaCobro.ANUAL)) == [anual]
    hoy = timezone.localdate()
    assert selectores.filtrar_cuentas_cobro(usuario_administrador, desde=hoy, hasta=hoy).count() == 2
    assert not selectores.filtrar_cuentas_cobro(usuario_administrador, hasta=date(2000, 1, 1)).exists()


def test_sugerencia_sin_honorario_propone_una_linea_por_servicio(cliente_con_servicios):
    sugerencia = selectores.sugerencia_cuenta_cobro(cliente_con_servicios)
    assert sugerencia["valor_total"] == 0
    assert {linea["descripcion_linea"] for linea in sugerencia["lineas"]} == {
        "Contabilidad mensual",
        "Nómina",
    }
    assert all(linea["valor_linea"] is None for linea in sugerencia["lineas"])


def test_sugerencia_con_honorario_por_servicio_lleva_monto_por_linea(
    cliente_con_servicios, servicio_contabilidad, servicio_nomina, usuario_administrador
):
    servicios.configurar_honorario(
        cliente_con_servicios,
        Honorario.POR_SERVICIO,
        None,
        {servicio_contabilidad: Decimal("600000"), servicio_nomina: Decimal("250000")},
        usuario_administrador,
    )
    sugerencia = selectores.sugerencia_cuenta_cobro(cliente_con_servicios)
    assert sugerencia["valor_total"] == Decimal("850000")
    montos = {linea["descripcion_linea"]: linea["valor_linea"] for linea in sugerencia["lineas"]}
    assert montos == {"Contabilidad mensual": Decimal("600000"), "Nómina": Decimal("250000")}


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(Decimal("1200000"), "$ 1.200.000"), (Decimal("999.50"), "$ 1.000"), (0, "$ 0"), (None, "$ 0")],
)
def test_formato_pesos(valor, esperado):
    assert formato_pesos(valor) == esperado
