"""Pruebas del proceso automático de cobro (comando `procesar_cobros`) con fechas simuladas."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from io import StringIO

import pytest
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from aplicaciones.finanzas import servicios
from aplicaciones.finanzas.models import (
    CORREO,
    WHATSAPP,
    ConfiguracionCobro,
    CuentaCobro,
    EnvioProgramado,
    Honorario,
)

pytestmark = pytest.mark.django_db


def _momento(anio, mes, dia, hora=8):
    """Fecha y hora simulada en la zona horaria del proyecto (Bogotá)."""
    return timezone.make_aware(datetime(anio, mes, dia, hora, 0))


@pytest.fixture
def configuracion(cuenta_bancaria, metodo_transferencia):
    configuracion = ConfiguracionCobro.obtener()
    configuracion.cobro_automatico_activo = True
    configuracion.dia_generacion = 5
    configuracion.dias_plazo_pago = 10
    configuracion.canal_cobro = CORREO
    configuracion.cuenta_bancaria = cuenta_bancaria
    configuracion.metodo_pago = metodo_transferencia
    configuracion.recordatorios_activos = True
    configuracion.dias_antes_vencimiento = 3
    configuracion.frecuencia_mora_dias = 7
    configuracion.canal_recordatorio = CORREO
    configuracion.save()
    return configuracion


@pytest.fixture
def cliente_con_honorario(cliente, usuario_administrador, despacho):
    servicios.configurar_honorario(
        cliente, Honorario.FIJO_MENSUAL, Decimal("900000"), {}, usuario_administrador
    )
    return cliente


# ---------------------------------------------------------------------------
# Cobro mensual automático
# ---------------------------------------------------------------------------


def test_cobro_mensual_no_se_genera_antes_del_dia_configurado(configuracion, cliente_con_honorario):
    resumen = servicios.procesar_cobros(_momento(2026, 10, 4))
    assert resumen["cuentas_generadas"] == 0
    assert not CuentaCobro.objects.exists()


def test_cobro_mensual_genera_y_envia_una_sola_vez_por_mes(
    configuracion, cliente_con_honorario, cliente_junior
):
    resumen = servicios.procesar_cobros(_momento(2026, 10, 5))

    cuenta = CuentaCobro.objects.get()  # el cliente del Junior no tiene honorario: no se le cobra
    assert resumen["cuentas_generadas"] == 1
    assert resumen["correos_enviados"] == 1
    assert cuenta.cliente == cliente_con_honorario
    assert cuenta.valor_total == Decimal("900000")
    assert cuenta.fecha_inicio_periodo == date(2026, 10, 1)
    assert cuenta.fecha_fin_periodo == date(2026, 10, 31)
    assert cuenta.fecha_vencimiento_pago == date(2026, 10, 15)
    assert cuenta.cuenta_bancaria == configuracion.cuenta_bancaria
    assert cuenta.estado_envio == CuentaCobro.ENVIADA
    assert len(mail.outbox) == 1

    # Correr de nuevo el mismo mes (el cron corre cada 15 minutos) no duplica nada.
    segundo = servicios.procesar_cobros(_momento(2026, 10, 20))
    assert segundo["cuentas_generadas"] == 0
    assert CuentaCobro.objects.count() == 1

    # El mes siguiente sí genera la nueva cuenta.
    servicios.procesar_cobros(_momento(2026, 11, 5))
    assert CuentaCobro.objects.count() == 2


def test_cobro_mensual_desactivado_no_genera(configuracion, cliente_con_honorario):
    configuracion.cobro_automatico_activo = False
    configuracion.save()
    assert servicios.procesar_cobros(_momento(2026, 10, 5))["cuentas_generadas"] == 0


def test_cobro_mensual_por_whatsapp_queda_en_bandeja(configuracion, cliente_con_honorario):
    configuracion.canal_cobro = WHATSAPP
    configuracion.save()
    resumen = servicios.procesar_cobros(_momento(2026, 10, 5))
    assert resumen["whatsapp_pendientes"] == 1
    assert EnvioProgramado.objects.get().estado == EnvioProgramado.PENDIENTE_WHATSAPP
    assert len(mail.outbox) == 0


def test_cobro_mensual_no_incluye_clientes_inactivos(configuracion, cliente_con_honorario):
    cliente_con_honorario.inactivar()
    assert servicios.procesar_cobros(_momento(2026, 10, 5))["cuentas_generadas"] == 0


# ---------------------------------------------------------------------------
# Vencidas y recordatorios automáticos
# ---------------------------------------------------------------------------


@pytest.fixture
def cuenta_que_vence_el_20(generar_cuenta, cliente):
    return generar_cuenta(cliente, fecha_vencimiento_pago=date(2026, 10, 20))


def test_marca_como_vencidas_las_cuentas_con_saldo(configuracion, cuenta_que_vence_el_20):
    servicios.procesar_cobros(_momento(2026, 10, 20))
    cuenta_que_vence_el_20.refresh_from_db()
    assert cuenta_que_vence_el_20.estado_pago == CuentaCobro.PAGO_PENDIENTE

    resumen = servicios.procesar_cobros(_momento(2026, 10, 21))
    cuenta_que_vence_el_20.refresh_from_db()
    assert resumen["cuentas_vencidas"] == 1
    assert cuenta_que_vence_el_20.estado_pago == CuentaCobro.VENCIDA


def test_no_marca_vencida_una_cuenta_pagada_en_su_totalidad(
    configuracion, cuenta_que_vence_el_20, usuario_administrador
):
    cuenta_que_vence_el_20.abonos.create(
        monto=Decimal("1000000"),
        responsable=usuario_administrador,
        saldo_anterior=Decimal("1000000"),
        saldo_resultante=Decimal("0"),
    )
    assert servicios.procesar_cobros(_momento(2026, 10, 25))["cuentas_vencidas"] == 0


def test_recordatorio_antes_del_vencimiento_una_sola_vez(configuracion, cuenta_que_vence_el_20):
    assert servicios.procesar_cobros(_momento(2026, 10, 16))["recordatorios_programados"] == 0
    assert servicios.procesar_cobros(_momento(2026, 10, 17))["recordatorios_programados"] == 1
    assert servicios.procesar_cobros(_momento(2026, 10, 18))["recordatorios_programados"] == 0
    assert len(mail.outbox) == 1
    assert "vence el" in mail.outbox[0].body


def test_recordatorios_en_mora_cada_frecuencia(configuracion, cuenta_que_vence_el_20):
    servicios.procesar_cobros(_momento(2026, 10, 17))  # recordatorio previo al vencimiento
    # En mora: el primero sale cuando pasó la frecuencia desde el último.
    assert servicios.procesar_cobros(_momento(2026, 10, 22))["recordatorios_programados"] == 0
    assert servicios.procesar_cobros(_momento(2026, 10, 24))["recordatorios_programados"] == 1
    assert servicios.procesar_cobros(_momento(2026, 10, 28))["recordatorios_programados"] == 0
    assert servicios.procesar_cobros(_momento(2026, 10, 31))["recordatorios_programados"] == 1
    assert "venció" in mail.outbox[-1].body


def test_recordatorios_desactivados(configuracion, cuenta_que_vence_el_20):
    configuracion.recordatorios_activos = False
    configuracion.save()
    assert servicios.procesar_cobros(_momento(2026, 10, 25))["recordatorios_programados"] == 0


def test_procesar_registra_la_ultima_ejecucion(configuracion):
    momento = _momento(2026, 10, 5)
    servicios.procesar_cobros(momento)
    configuracion.refresh_from_db()
    assert configuracion.ultima_ejecucion == momento


def test_comando_procesar_cobros(configuracion, cliente_con_honorario, monkeypatch):
    monkeypatch.setattr(timezone, "now", lambda: _momento(2026, 10, 5))
    salida = StringIO()
    call_command("procesar_cobros", stdout=salida)
    assert "Cuentas generadas: 1" in salida.getvalue()
    assert "Proceso de cobro terminado" in salida.getvalue()


def test_configuracion_obtener_crea_una_sola_fila(db):
    assert ConfiguracionCobro.obtener().pk == ConfiguracionCobro.obtener().pk
    assert ConfiguracionCobro.objects.count() == 1
    assert str(ConfiguracionCobro.obtener()) == "Configuración del cobro automático"


def test_envio_programado_str(cuenta_cliente):
    [envio] = servicios.programar_envio(
        cuenta_cliente, EnvioProgramado.RECORDATORIO, CORREO, timezone.now() + timedelta(days=1)
    )
    assert "Recordatorio por Correo" in str(envio)
