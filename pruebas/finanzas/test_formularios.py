"""Pruebas de los formularios del módulo 6: honorarios y cuentas de cobro."""

from datetime import date
from decimal import Decimal

import pytest

from aplicaciones.finanzas.formularios import CuentaCobroForm, HonorarioForm, LineasCobroFormSet
from aplicaciones.finanzas.models import CuentaCobro, Honorario

pytestmark = pytest.mark.django_db


def _datos_lineas(*lineas):
    datos = {"lineas-TOTAL_FORMS": str(len(lineas)), "lineas-INITIAL_FORMS": "0"}
    for indice, (descripcion, valor) in enumerate(lineas):
        datos[f"lineas-{indice}-descripcion_linea"] = descripcion
        datos[f"lineas-{indice}-valor_linea"] = valor
    return datos


def _formset(*lineas, valor_total=Decimal("1000000")):
    formset = LineasCobroFormSet(_datos_lineas(*lineas), prefix="lineas")
    formset.valor_total = valor_total
    return formset


# ---------------------------------------------------------------------------
# Líneas de la cuenta de cobro (HU049)
# ---------------------------------------------------------------------------


def test_lineas_sin_valores_individuales_son_validas():
    formset = _formset(("Contabilidad", ""), ("Nómina", ""))
    assert formset.is_valid()
    assert [linea["descripcion_linea"] for linea in formset.lineas()] == ["Contabilidad", "Nómina"]


def test_lineas_con_valores_deben_sumar_el_total():
    assert _formset(("Contabilidad", "700000"), ("Nómina", "300000")).is_valid()
    formset = _formset(("Contabilidad", "700000"), ("Nómina", "200000"))
    assert not formset.is_valid()
    assert "debe ser igual al valor total" in str(formset.non_form_errors())


def test_se_exige_al_menos_una_linea():
    formset = _formset(("", ""))
    assert not formset.is_valid()
    assert "al menos una línea" in str(formset.non_form_errors())


def test_linea_con_valor_sin_descripcion_no_es_valida():
    formset = _formset(("Contabilidad", "1000000"), ("", "5000"))
    assert not formset.is_valid()


def test_linea_con_concepto_sin_descripcion_toma_el_nombre_del_concepto(concepto_revisoria):
    datos = _datos_lineas(("", ""))
    datos["lineas-0-concepto"] = str(concepto_revisoria.pk)
    formset = LineasCobroFormSet(datos, prefix="lineas")
    formset.valor_total = Decimal("300000")
    assert formset.is_valid()
    assert formset.lineas()[0]["descripcion_linea"] == "Revisoría fiscal"


# ---------------------------------------------------------------------------
# Datos generales de la cuenta de cobro
# ---------------------------------------------------------------------------


def _datos_cuenta(cliente, **extra):
    datos = {
        "cliente": cliente.pk,
        "periodo_facturado": CuentaCobro.TRIMESTRAL,
        "fecha_inicio_periodo": "2026-01-01",
        "valor_total": "1000000",
        "fecha_vencimiento_pago": "2026-04-10",
    }
    datos.update(extra)
    return datos


def test_cuenta_cobro_calcula_fin_del_periodo(cliente, usuario_administrador):
    formulario = CuentaCobroForm(_datos_cuenta(cliente), usuario=usuario_administrador)
    assert formulario.is_valid(), formulario.errors
    assert formulario.cleaned_data["fecha_fin_periodo"] == date(2026, 3, 31)


def test_periodo_personalizado_exige_fecha_final_valida(cliente, usuario_administrador):
    sin_fin = CuentaCobroForm(
        _datos_cuenta(cliente, periodo_facturado=CuentaCobro.PERSONALIZADO), usuario=usuario_administrador
    )
    assert "fecha_fin_periodo" in sin_fin.errors
    invertido = CuentaCobroForm(
        _datos_cuenta(cliente, periodo_facturado=CuentaCobro.PERSONALIZADO, fecha_fin_periodo="2025-12-01"),
        usuario=usuario_administrador,
    )
    assert "fecha_fin_periodo" in invertido.errors


def test_valor_total_debe_ser_positivo(cliente, usuario_administrador):
    formulario = CuentaCobroForm(_datos_cuenta(cliente, valor_total="0"), usuario=usuario_administrador)
    assert "valor_total" in formulario.errors


def test_cuenta_cobro_no_acepta_cliente_inactivo(cliente, usuario_administrador):
    cliente.inactivar()
    formulario = CuentaCobroForm(_datos_cuenta(cliente), usuario=usuario_administrador)
    assert "cliente" in formulario.errors


# ---------------------------------------------------------------------------
# Honorario (HU044)
# ---------------------------------------------------------------------------


def test_honorario_fijo_exige_monto(cliente):
    formulario = HonorarioForm({"tipo": Honorario.FIJO_MENSUAL, "monto": ""}, cliente=cliente)
    assert "monto" in formulario.errors


def test_honorario_por_servicio_crea_un_campo_por_servicio(cliente_con_servicios, servicio_contabilidad):
    formulario = HonorarioForm(
        {"tipo": Honorario.POR_SERVICIO, f"servicio_{servicio_contabilidad.pk}": "600000"},
        cliente=cliente_con_servicios,
    )
    assert formulario.is_valid(), formulario.errors
    assert len(formulario.campos_servicio()) == 2
    assert formulario.montos_por_servicio()[servicio_contabilidad] == Decimal("600000")


def test_honorario_por_servicio_exige_algun_monto(cliente_con_servicios):
    formulario = HonorarioForm({"tipo": Honorario.POR_SERVICIO}, cliente=cliente_con_servicios)
    assert not formulario.is_valid()
    assert "al menos un servicio" in str(formulario.non_field_errors())


def test_honorario_por_servicio_sin_servicios_no_es_valido(cliente):
    formulario = HonorarioForm({"tipo": Honorario.POR_SERVICIO}, cliente=cliente)
    assert not formulario.is_valid()
    assert "no tiene tipos de servicio" in str(formulario.non_field_errors())
