"""
Pruebas de abonos y cartera del módulo 6 (HU016-HU018), incluido el
disparador de PostgreSQL que calcula saldos y protege la trazabilidad.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Table

from aplicaciones.finanzas import selectores, servicios
from aplicaciones.finanzas.models import Abono, CuentaCobro, MetodoPago

pytestmark = pytest.mark.django_db


def _abonar(cuenta, monto, usuario, metodo=None, fecha=None):
    return servicios.registrar_abono(
        cuenta, fecha=fecha or timezone.localdate(), monto=Decimal(monto), metodo_pago=metodo, usuario=usuario
    )


# ---------------------------------------------------------------------------
# Disparador de PostgreSQL
# ---------------------------------------------------------------------------


def test_disparador_calcula_saldos_ignorando_los_valores_enviados(cuenta_cliente, usuario_administrador):
    abono = Abono.objects.create(
        cuenta_cobro=cuenta_cliente,
        monto=Decimal("300000"),
        responsable=usuario_administrador,
        saldo_anterior=Decimal("999"),
        saldo_resultante=Decimal("999"),
    )
    abono.refresh_from_db()
    assert abono.saldo_anterior == Decimal("1000000")
    assert abono.saldo_resultante == Decimal("700000")


def test_abonos_sucesivos_encadenan_saldos_y_estados(
    cuenta_cliente, usuario_administrador, metodo_transferencia
):
    primero = _abonar(cuenta_cliente, "400000", usuario_administrador, metodo_transferencia)
    assert (primero.saldo_anterior, primero.saldo_resultante) == (Decimal("1000000"), Decimal("600000"))
    assert cuenta_cliente.estado_pago == CuentaCobro.ABONADA

    segundo = _abonar(cuenta_cliente, "600000", usuario_administrador, metodo_transferencia)
    assert (segundo.saldo_anterior, segundo.saldo_resultante) == (Decimal("600000"), Decimal("0"))
    assert cuenta_cliente.estado_pago == CuentaCobro.PAGADA
    assert cuenta_cliente.saldo_pendiente == 0


def test_abono_parcial_de_cuenta_vencida_la_deja_vencida(generar_cuenta, cliente, usuario_administrador):
    cuenta = generar_cuenta(cliente, fecha_vencimiento_pago=timezone.localdate() - timedelta(days=5))
    _abonar(cuenta, "100000", usuario_administrador)
    assert cuenta.estado_pago == CuentaCobro.VENCIDA


def test_disparador_rechaza_monto_mayor_que_el_saldo(cuenta_cliente, usuario_administrador):
    with pytest.raises(ValueError, match="supera el saldo pendiente"):
        _abonar(cuenta_cliente, "1000001", usuario_administrador)
    assert not Abono.objects.exists()
    cuenta_cliente.refresh_from_db()
    assert cuenta_cliente.estado_pago == CuentaCobro.PAGO_PENDIENTE


def test_disparador_rechaza_monto_no_positivo(cuenta_cliente, usuario_administrador):
    with pytest.raises(IntegrityError), transaction.atomic():
        Abono.objects.create(
            cuenta_cobro=cuenta_cliente,
            monto=Decimal("0"),
            responsable=usuario_administrador,
            saldo_anterior=0,
            saldo_resultante=0,
        )


def test_abonos_no_se_modifican_ni_se_eliminan(cuenta_cliente, usuario_administrador):
    abono = _abonar(cuenta_cliente, "100000", usuario_administrador)
    with pytest.raises(IntegrityError), transaction.atomic():
        Abono.objects.filter(pk=abono.pk).update(monto=Decimal("1"))
    with pytest.raises(IntegrityError), transaction.atomic():
        abono.delete()
    assert Abono.objects.get(pk=abono.pk).monto == Decimal("100000")


def test_registrar_abono_con_medio_de_pago_nuevo_lo_agrega_al_catalogo(cuenta_cliente, usuario_administrador):
    abono = servicios.registrar_abono(
        cuenta_cliente,
        fecha=timezone.localdate(),
        monto=Decimal("50000"),
        metodo_pago=None,
        metodo_nuevo="  Bre-B  ",
        usuario=usuario_administrador,
    )
    assert abono.metodo_pago == MetodoPago.objects.get(nombre_metodo="Bre-B")


# ---------------------------------------------------------------------------
# Selectores: historial, saldo y cartera
# ---------------------------------------------------------------------------


def test_historial_de_abonos_del_mas_reciente_al_mas_antiguo(cuenta_cliente, cliente, usuario_administrador):
    antiguo = _abonar(cuenta_cliente, "100000", usuario_administrador, fecha=date(2026, 9, 1))
    reciente = _abonar(cuenta_cliente, "200000", usuario_administrador, fecha=date(2026, 9, 10))
    assert list(selectores.abonos_del_cliente(usuario_administrador, cliente)) == [reciente, antiguo]


def test_junior_no_ve_abonos_de_clientes_ajenos(
    cuenta_cliente, cliente, usuario_junior, usuario_administrador
):
    _abonar(cuenta_cliente, "100000", usuario_administrador)
    assert not selectores.abonos_del_cliente(usuario_junior, cliente).exists()


def test_saldo_del_cliente_suma_todas_sus_cuentas(generar_cuenta, cliente, usuario_administrador):
    primera = generar_cuenta(cliente, valor_total=Decimal("1000000"))
    generar_cuenta(cliente, valor_total=Decimal("500000"))
    _abonar(primera, "300000", usuario_administrador)
    assert selectores.saldo_del_cliente(cliente) == Decimal("1200000")


def test_cartera_ordena_por_mora_y_marca_mora_critica(
    generar_cuenta, cliente, cliente_junior, usuario_administrador
):
    hoy = date(2026, 12, 1)
    generar_cuenta(cliente, fecha_vencimiento_pago=date(2026, 11, 25))  # 6 días de mora
    generar_cuenta(
        cliente_junior, valor_total=Decimal("500000"), fecha_vencimiento_pago=date(2026, 10, 1)
    )  # 61 días

    filas = selectores.cartera(usuario_administrador, hoy=hoy)
    assert [fila["cliente"] for fila in filas] == [cliente_junior, cliente]
    assert filas[0]["dias_mora"] == 61
    assert filas[0]["mora_critica"] is True
    assert filas[1]["mora_critica"] is False
    assert selectores.totales_cartera(filas)["saldo"] == Decimal("1500000")


def test_cartera_excluye_clientes_al_dia_salvo_que_se_pidan(generar_cuenta, cliente, usuario_administrador):
    cuenta = generar_cuenta(cliente)
    _abonar(cuenta, "1000000", usuario_administrador)
    assert selectores.cartera(usuario_administrador) == []
    [fila] = selectores.cartera(usuario_administrador, solo_con_saldo=False)
    assert fila["cobrado"] == Decimal("1000000")
    assert fila["saldo"] == 0


def test_cartera_del_senior_solo_incluye_sus_clientes(cuenta_cliente, usuario_senior):
    assert selectores.cartera(usuario_senior) == []


# ---------------------------------------------------------------------------
# Vistas
# ---------------------------------------------------------------------------


def _datos_abono(monto="250000", **extra):
    datos = {"fecha": timezone.localdate().isoformat(), "monto": monto, "metodo_nuevo": "Transferencia"}
    datos.update(extra)
    return datos


def test_administrador_registra_abono_desde_el_detalle(client, usuario_administrador, cuenta_cliente):
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("finanzas:registrar_abono", args=[cuenta_cliente.pk]), _datos_abono(), follow=True
    )
    assert "saldo actual $ 750.000" in respuesta.content.decode()
    abono = Abono.objects.get()
    assert abono.responsable == usuario_administrador
    assert abono.saldo_resultante == Decimal("750000")


@pytest.mark.parametrize("usuario_fixture", ["usuario_senior", "usuario_junior"])
def test_senior_y_junior_no_registran_abonos(client, request, usuario_fixture, cuenta_cliente_junior):
    client.force_login(request.getfixturevalue(usuario_fixture))
    respuesta = client.post(
        reverse("finanzas:registrar_abono", args=[cuenta_cliente_junior.pk]), _datos_abono()
    )
    assert respuesta.status_code == 403
    assert not Abono.objects.exists()


@pytest.mark.parametrize(
    ("datos", "mensaje"),
    [
        (_datos_abono(monto="2000000"), "supera el saldo pendiente"),
        (_datos_abono(fecha=(date.today() + timedelta(days=5)).isoformat()), "no puede ser futura"),
        (_datos_abono(metodo_nuevo=""), "Indique el medio de pago"),
    ],
)
def test_abono_invalido_muestra_el_error(client, usuario_administrador, cuenta_cliente, datos, mensaje):
    client.force_login(usuario_administrador)
    respuesta = client.post(reverse("finanzas:registrar_abono", args=[cuenta_cliente.pk]), datos, follow=True)
    assert mensaje in respuesta.content.decode()
    assert not Abono.objects.exists()


def test_detalle_muestra_pagos_y_oculta_formulario_si_esta_pagada(
    client, usuario_administrador, cuenta_cliente
):
    _abonar(cuenta_cliente, "1000000", usuario_administrador)
    client.force_login(usuario_administrador)
    contenido = client.get(reverse("finanzas:detalle", args=[cuenta_cliente.pk])).content.decode()
    assert "Pagos y abonos" in contenido
    assert reverse("finanzas:registrar_abono", args=[cuenta_cliente.pk]) not in contenido


@pytest.mark.parametrize("usuario_fixture", ["usuario_administrador", "usuario_senior", "usuario_junior"])
def test_todos_los_roles_consultan_la_cartera(client, request, usuario_fixture):
    client.force_login(request.getfixturevalue(usuario_fixture))
    assert client.get(reverse("finanzas:cartera")).status_code == 200


def test_junior_ve_en_cartera_solo_su_cliente(client, usuario_junior, cuenta_cliente, cuenta_cliente_junior):
    client.force_login(usuario_junior)
    filas = client.get(reverse("finanzas:cartera")).context["filas"]
    assert [fila["cliente"] for fila in filas] == [cuenta_cliente_junior.cliente]


def test_ficha_del_cliente_muestra_saldo_e_historial_de_abonos(
    client, usuario_junior, usuario_administrador, cuenta_cliente_junior
):
    _abonar(cuenta_cliente_junior, "200000", usuario_administrador)
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("clientes:detalle", args=[cuenta_cliente_junior.cliente.pk]))
    assert respuesta.context["saldo_cliente"] == Decimal("300000")
    assert len(respuesta.context["abonos"]) == 1
    assert "Historial de abonos" in respuesta.content.decode()


# ---------------------------------------------------------------------------
# Abonos en las tablas de Honorarios y en el PDF de la cuenta de cobro
# ---------------------------------------------------------------------------


def test_con_abonos_anota_abonado_saldo_y_abonos_en_orden(cuenta_cliente, usuario_administrador):
    _abonar(cuenta_cliente, "300000", usuario_administrador, fecha=date(2026, 9, 10))
    _abonar(cuenta_cliente, "100000", usuario_administrador, fecha=date(2026, 9, 1))
    cuenta = selectores.con_abonos(CuentaCobro.objects.filter(pk=cuenta_cliente.pk)).get()
    assert cuenta.abonado == Decimal("400000")
    assert cuenta.saldo == Decimal("600000")
    assert [abono.fecha for abono in cuenta.abonos.all()] == [date(2026, 9, 1), date(2026, 9, 10)]


def test_historico_muestra_abonado_saldo_y_detalle_de_abonos(client, usuario_administrador, cuenta_cliente):
    _abonar(cuenta_cliente, "250000", usuario_administrador)
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("finanzas:historico"))
    cuenta = respuesta.context["cuentas"][0]
    assert (cuenta.abonado, cuenta.saldo) == (Decimal("250000"), Decimal("750000"))
    contenido = respuesta.content.decode()
    assert "$ 250.000" in contenido and "$ 750.000" in contenido
    assert f'id="abonos-cuenta-{cuenta_cliente.pk}"' in contenido


def test_ficha_del_cliente_muestra_abonado_y_saldo_por_cuenta(client, usuario_administrador, cuenta_cliente):
    _abonar(cuenta_cliente, "400000", usuario_administrador)
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("clientes:detalle", args=[cuenta_cliente.cliente.pk]))
    assert respuesta.context["cuentas_cobro"][0].saldo == Decimal("600000")
    assert f'id="abonos-cuenta-{cuenta_cliente.pk}"' in respuesta.content.decode()


def test_pdf_sin_abonos_no_trae_seccion_de_abonos(cuenta_cliente):
    assert servicios._seccion_abonos_pdf(cuenta_cliente, getSampleStyleSheet(), 16 * cm) == []


def test_pdf_muestra_abonos_y_saldo_pendiente(cuenta_cliente, usuario_administrador, metodo_transferencia):
    _abonar(cuenta_cliente, "300000", usuario_administrador, metodo=metodo_transferencia)
    elementos = servicios._seccion_abonos_pdf(cuenta_cliente, getSampleStyleSheet(), 16 * cm)
    tabla = next(elemento for elemento in elementos if isinstance(elemento, Table))
    filas = tabla._cellvalues
    assert filas[1][1].text == metodo_transferencia.nombre_metodo
    assert filas[1][2] == "$ 300.000"
    assert filas[-2][1:] == ["Total abonado", "$ 300.000"]
    assert filas[-1][1:] == ["SALDO PENDIENTE POR PAGAR", "$ 700.000"]


def test_pdf_de_cuenta_pagada_lo_indica(cuenta_cliente, usuario_administrador):
    _abonar(cuenta_cliente, "1000000", usuario_administrador)
    elementos = servicios._seccion_abonos_pdf(cuenta_cliente, getSampleStyleSheet(), 16 * cm)
    textos = [elemento.text for elemento in elementos if isinstance(elemento, Paragraph)]
    assert any("pagada en su totalidad" in texto for texto in textos)


def test_registrar_abono_regenera_el_pdf(cuenta_cliente, usuario_administrador):
    with cuenta_cliente.archivo.open("rb") as archivo:
        antes = archivo.read()
    _abonar(cuenta_cliente, "300000", usuario_administrador)
    cuenta_cliente.refresh_from_db()
    assert cuenta_cliente.archivo.name.endswith(f"cuenta_cobro_{cuenta_cliente.pk}.pdf")
    with cuenta_cliente.archivo.open("rb") as archivo:
        despues = archivo.read()
    assert despues.startswith(b"%PDF") and despues != antes


def test_historico_con_abonos_conserva_el_orden_de_la_mas_reciente(
    client, generar_cuenta, cliente, usuario_administrador
):
    primera = generar_cuenta(cliente)
    segunda = generar_cuenta(cliente)
    _abonar(primera, "100000", usuario_administrador)
    client.force_login(usuario_administrador)
    assert list(client.get(reverse("finanzas:historico")).context["cuentas"]) == [segunda, primera]
