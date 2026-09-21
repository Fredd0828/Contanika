"""Pruebas de los modelos del módulo 6: honorarios, cuentas de cobro y abonos."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from aplicaciones.finanzas.models import Abono, CuentaCobro, Honorario

pytestmark = pytest.mark.django_db


@pytest.fixture
def cuenta_cobro(cliente):
    honorario = Honorario.objects.create(cliente=cliente, monto=Decimal("500000"))
    return CuentaCobro.objects.create(
        cliente=cliente,
        honorario=honorario,
        valor_total=Decimal("500000"),
        fecha_vencimiento_pago=date.today() + timedelta(days=15),
    )


def test_cuenta_cobro_sin_abonos(cuenta_cobro):
    """Sin abonos, el saldo pendiente es el valor total de la cuenta."""
    assert cuenta_cobro.total_abonado == 0
    assert cuenta_cobro.saldo_pendiente == Decimal("500000")


def test_abono_actualiza_el_saldo_pendiente(cuenta_cobro, usuario_administrador):
    """Un abono parcial reduce el saldo pendiente de la cuenta."""
    Abono.objects.create(
        cuenta_cobro=cuenta_cobro,
        monto=Decimal("200000"),
        responsable=usuario_administrador,
        saldo_anterior=Decimal("500000"),
        saldo_resultante=Decimal("300000"),
    )
    assert cuenta_cobro.total_abonado == Decimal("200000")
    assert cuenta_cobro.saldo_pendiente == Decimal("300000")


def test_cuenta_en_mora(cuenta_cobro):
    """Una cuenta vencida con saldo pendiente se marca en mora."""
    CuentaCobro.objects.filter(pk=cuenta_cobro.pk).update(
        fecha_vencimiento_pago=date.today() - timedelta(days=1)
    )
    cuenta_cobro.refresh_from_db()
    assert cuenta_cobro.esta_en_mora is True


def test_cuenta_pagada_no_esta_en_mora(cliente, usuario_administrador):
    """Una cuenta pagada en su totalidad no se marca en mora."""
    honorario = Honorario.objects.create(cliente=cliente, monto=Decimal("300000"))
    cuenta = CuentaCobro.objects.create(
        cliente=cliente,
        honorario=honorario,
        valor_total=Decimal("300000"),
        fecha_vencimiento_pago=date.today() - timedelta(days=1),
    )
    Abono.objects.create(
        cuenta_cobro=cuenta,
        monto=Decimal("300000"),
        responsable=usuario_administrador,
        saldo_anterior=Decimal("300000"),
        saldo_resultante=Decimal("0"),
    )
    assert cuenta.saldo_pendiente == 0
    assert cuenta.esta_en_mora is False
