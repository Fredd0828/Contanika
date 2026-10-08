"""Pruebas de los servicios del módulo 6: honorarios, catálogos y cuentas de cobro."""

from datetime import date
from decimal import Decimal

import pytest

from aplicaciones.finanzas import servicios
from aplicaciones.finanzas.models import (
    Abono,
    ConceptoFacturable,
    CuentaCobro,
    CuentaCobroDetalle,
    Honorario,
    HonorarioServicio,
    MetodoPago,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Honorario
# ---------------------------------------------------------------------------


def test_configurar_honorario_fijo_guarda_monto_y_usuario(cliente, usuario_administrador):
    honorario = servicios.configurar_honorario(
        cliente, Honorario.FIJO_MENSUAL, Decimal("800000"), {}, usuario_administrador
    )
    assert honorario.monto == Decimal("800000")
    assert honorario.usuario_actualizacion == usuario_administrador
    assert honorario.fecha_actualizacion is not None


def test_configurar_honorario_por_servicio_suma_los_montos(
    cliente_con_servicios, servicio_contabilidad, servicio_nomina, usuario_administrador
):
    honorario = servicios.configurar_honorario(
        cliente_con_servicios,
        Honorario.POR_SERVICIO,
        None,
        {servicio_contabilidad: Decimal("600000"), servicio_nomina: Decimal("250000")},
        usuario_administrador,
    )
    assert honorario.monto == Decimal("850000")
    assert honorario.servicios.count() == 2


def test_cambiar_honorario_a_fijo_descarta_montos_por_servicio(
    cliente_con_servicios, servicio_contabilidad, usuario_administrador
):
    servicios.configurar_honorario(
        cliente_con_servicios,
        Honorario.POR_SERVICIO,
        None,
        {servicio_contabilidad: Decimal("600000")},
        usuario_administrador,
    )
    honorario = servicios.configurar_honorario(
        cliente_con_servicios, Honorario.FIJO_MENSUAL, Decimal("900000"), {}, usuario_administrador
    )
    assert honorario.monto == Decimal("900000")
    assert not HonorarioServicio.objects.exists()


def test_cambiar_honorario_no_afecta_cuentas_ya_generadas(cliente, usuario_administrador, generar_cuenta):
    servicios.configurar_honorario(
        cliente, Honorario.FIJO_MENSUAL, Decimal("1000000"), {}, usuario_administrador
    )
    cuenta = generar_cuenta(cliente, valor_total=Decimal("1000000"))
    servicios.configurar_honorario(
        cliente, Honorario.FIJO_MENSUAL, Decimal("2000000"), {}, usuario_administrador
    )
    cuenta.refresh_from_db()
    assert cuenta.valor_total == Decimal("1000000")


# ---------------------------------------------------------------------------
# Cuentas de cobro
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("periodo", "fin_esperado"),
    [
        (CuentaCobro.MENSUAL, date(2026, 1, 31)),
        (CuentaCobro.BIMESTRAL, date(2026, 2, 28)),
        (CuentaCobro.TRIMESTRAL, date(2026, 3, 31)),
        (CuentaCobro.SEMESTRAL, date(2026, 6, 30)),
        (CuentaCobro.ANUAL, date(2026, 12, 31)),
        (CuentaCobro.PERSONALIZADO, None),
    ],
)
def test_calcular_fin_periodo(periodo, fin_esperado):
    assert servicios.calcular_fin_periodo(periodo, date(2026, 1, 1)) == fin_esperado


def test_generar_cuenta_cobro_crea_lineas_en_orden_y_pdf(
    cliente, generar_cuenta, concepto_revisoria, cuenta_bancaria, metodo_transferencia
):
    cuenta = generar_cuenta(
        cliente,
        valor_total=Decimal("1000000"),
        cuenta_bancaria=cuenta_bancaria,
        metodo_pago=metodo_transferencia,
        lineas=[
            {"descripcion_linea": "Contabilidad mensual", "valor_linea": Decimal("700000")},
            {
                "descripcion_linea": "Revisoría fiscal",
                "concepto": concepto_revisoria,
                "valor_linea": Decimal("300000"),
            },
        ],
    )
    lineas = list(
        CuentaCobroDetalle.objects.filter(cuenta_cobro=cuenta).values_list("descripcion_linea", flat=True)
    )
    assert lineas == ["Contabilidad mensual", "Revisoría fiscal"]
    assert cuenta.detalles.get(descripcion_linea="Revisoría fiscal").concepto == concepto_revisoria
    assert cuenta.archivo.name.endswith(f"cuenta_cobro_{cuenta.pk}.pdf")
    with cuenta.archivo.open("rb") as archivo:
        assert archivo.read(5) == b"%PDF-"


def test_generar_cuenta_cobro_asocia_el_honorario_vigente(cliente, usuario_administrador, generar_cuenta):
    honorario = servicios.configurar_honorario(
        cliente, Honorario.FIJO_MENSUAL, Decimal("1000000"), {}, usuario_administrador
    )
    assert generar_cuenta(cliente).honorario == honorario


def test_pdf_de_cuenta_cobro_escapa_texto_capturado(cliente, generar_cuenta):
    cuenta = generar_cuenta(
        cliente, lineas=[{"descripcion_linea": "<b>Servicio</b> & <font>", "valor_linea": None}]
    )
    # Si el texto no se escapara, ReportLab fallaría al interpretar la etiqueta <font> incompleta.
    assert servicios.construir_pdf_cuenta_cobro(cuenta).startswith(b"%PDF-")


def test_eliminar_cuenta_cobro_borra_registro_y_archivo(cuenta_cliente):
    almacenamiento, nombre = cuenta_cliente.archivo.storage, cuenta_cliente.archivo.name
    servicios.eliminar_cuenta_cobro(cuenta_cliente)
    assert not CuentaCobro.objects.filter(pk=cuenta_cliente.pk).exists()
    assert not almacenamiento.exists(nombre)


def test_eliminar_cuenta_cobro_con_abonos_no_se_permite(cuenta_cliente, usuario_administrador):
    Abono.objects.create(
        cuenta_cobro=cuenta_cliente,
        monto=Decimal("100000"),
        responsable=usuario_administrador,
        saldo_anterior=Decimal("1000000"),
        saldo_resultante=Decimal("900000"),
    )
    with pytest.raises(ValueError):
        servicios.eliminar_cuenta_cobro(cuenta_cliente)
    assert CuentaCobro.objects.filter(pk=cuenta_cliente.pk).exists()


# ---------------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------------


def test_eliminar_elemento_de_catalogo_sin_uso(concepto_revisoria):
    servicios.eliminar_elemento_catalogo(concepto_revisoria)
    assert not ConceptoFacturable.objects.exists()


def test_eliminar_metodo_de_pago_usado_en_cuenta_no_se_permite(cliente, generar_cuenta, metodo_transferencia):
    generar_cuenta(cliente, metodo_pago=metodo_transferencia)
    with pytest.raises(ValueError):
        servicios.eliminar_elemento_catalogo(metodo_transferencia)
    assert MetodoPago.objects.filter(pk=metodo_transferencia.pk).exists()
