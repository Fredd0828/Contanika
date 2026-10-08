"""Pruebas de las alertas automáticas del Calendario (HU040): proceso, avisos y campana."""

from datetime import date, timedelta
from io import StringIO
from unittest import mock

import pytest
from django.core import mail
from django.core.management import call_command
from django.urls import reverse

from aplicaciones.calendario import selectores
from aplicaciones.calendario.models import ConfiguracionAlerta, Vencimiento
from aplicaciones.calendario.servicios import enlace_whatsapp_alerta, procesar_alertas
from aplicaciones.comunicaciones.models import Comunicacion

pytestmark = pytest.mark.django_db

HOY = date(2026, 3, 14)


@pytest.fixture
def vencimiento(cliente, usuario_administrador):
    """IVA que vence el 17 de marzo, a cargo de la administradora."""
    return Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="IVA bimestral",
        ambito=Vencimiento.NACIONAL,
        fecha_vencimiento=date(2026, 3, 17),
        responsable=usuario_administrador,
    )


def _alerta(vencimiento, dias=3, canal=ConfiguracionAlerta.CORREO):
    return ConfiguracionAlerta.objects.create(vencimiento=vencimiento, dias_anticipacion=dias, canal=canal)


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------


def test_fecha_aviso_es_el_vencimiento_menos_la_anticipacion(vencimiento):
    assert _alerta(vencimiento, dias=3).fecha_aviso == date(2026, 3, 14)


# ---------------------------------------------------------------------------
# procesar_alertas: correo
# ---------------------------------------------------------------------------


def test_envia_el_correo_al_responsable_y_registra_la_comunicacion(vencimiento, usuario_administrador):
    alerta = _alerta(vencimiento)

    resumen = procesar_alertas(hoy=HOY)

    assert resumen["correos_enviados"] == 1
    assert len(mail.outbox) == 1
    correo = mail.outbox[0]
    assert correo.to == [usuario_administrador.correo]
    assert "IVA bimestral" in correo.subject
    assert "vence en 3 días" in correo.body
    assert f"/calendario/vencimientos/{vencimiento.pk}/" in correo.body
    alerta.refresh_from_db()
    assert alerta.fecha_envio == HOY
    comunicacion = Comunicacion.objects.get(cliente=vencimiento.cliente)
    assert comunicacion.tipo == Comunicacion.AUTOMATICA
    assert comunicacion.canal == Comunicacion.CORREO
    assert comunicacion.modulo_origen == "Calendario"
    assert comunicacion.estado_envio == Comunicacion.EXITO
    assert comunicacion.usuario == usuario_administrador


def test_no_reenvia_una_alerta_ya_enviada(vencimiento):
    _alerta(vencimiento)
    procesar_alertas(hoy=HOY)
    resumen = procesar_alertas(hoy=HOY + timedelta(days=1))

    assert resumen["correos_enviados"] == 0
    assert len(mail.outbox) == 1


def test_no_envia_antes_de_la_fecha_de_aviso(vencimiento):
    _alerta(vencimiento)
    procesar_alertas(hoy=HOY - timedelta(days=1))
    assert mail.outbox == []


def test_no_envia_si_el_vencimiento_ya_esta_presentado(vencimiento):
    _alerta(vencimiento)
    vencimiento.estado_presentacion = Vencimiento.PRESENTADA
    vencimiento.save()
    procesar_alertas(hoy=HOY)
    assert mail.outbox == []


def test_no_envia_si_el_vencimiento_ya_paso(vencimiento):
    _alerta(vencimiento)
    procesar_alertas(hoy=date(2026, 3, 18))
    assert mail.outbox == []


def test_vuelve_a_avisar_si_la_fecha_del_vencimiento_se_corre(vencimiento):
    _alerta(vencimiento)
    procesar_alertas(hoy=HOY)

    vencimiento.fecha_vencimiento = date(2026, 3, 24)
    vencimiento.save()

    assert procesar_alertas(hoy=HOY)["correos_enviados"] == 0
    resumen = procesar_alertas(hoy=date(2026, 3, 21))
    assert resumen["correos_enviados"] == 1
    assert len(mail.outbox) == 2


def test_si_el_correo_falla_no_marca_la_alerta_y_se_reintenta(vencimiento):
    alerta = _alerta(vencimiento)
    with mock.patch("aplicaciones.calendario.servicios.send_mail", side_effect=OSError("SMTP caído")):
        resumen = procesar_alertas(hoy=HOY)

    assert resumen["correos_fallidos"] == 1
    alerta.refresh_from_db()
    assert alerta.fecha_envio is None
    assert not Comunicacion.objects.filter(cliente=vencimiento.cliente).exists()

    assert procesar_alertas(hoy=HOY)["correos_enviados"] == 1


def test_si_el_correo_falla_la_notificacion_interna_se_muestra_igual(vencimiento, usuario_administrador):
    _alerta(vencimiento)
    with mock.patch("aplicaciones.calendario.servicios.send_mail", side_effect=OSError("SMTP caído")):
        procesar_alertas(hoy=HOY)

    avisos = selectores.avisos_para_usuario(usuario_administrador, hoy=HOY)
    assert [a["vencimiento"] for a in avisos] == [vencimiento]


def test_sin_responsable_usa_el_del_cliente(cliente, usuario_administrador):
    vencimiento = Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="ICA",
        ambito=Vencimiento.MUNICIPAL,
        municipio="Bogotá D.C.",
        fecha_vencimiento=date(2026, 3, 17),
    )
    _alerta(vencimiento)
    procesar_alertas(hoy=HOY)
    assert mail.outbox[0].to == [cliente.responsable.correo]


# ---------------------------------------------------------------------------
# procesar_alertas: otros canales
# ---------------------------------------------------------------------------


def test_la_notificacion_interna_queda_registrada_sin_enviar_correo(vencimiento):
    alerta = _alerta(vencimiento, canal=ConfiguracionAlerta.NOTIFICACION)
    resumen = procesar_alertas(hoy=HOY)

    assert resumen["notificaciones"] == 1
    assert mail.outbox == []
    alerta.refresh_from_db()
    assert alerta.fecha_envio == HOY


def test_whatsapp_no_se_marca_como_enviada(vencimiento):
    alerta = _alerta(vencimiento, canal=ConfiguracionAlerta.WHATSAPP)
    procesar_alertas(hoy=HOY)

    assert mail.outbox == []
    alerta.refresh_from_db()
    assert alerta.fecha_envio is None


def test_enlace_whatsapp_usa_el_celular_del_responsable(vencimiento, usuario_administrador):
    usuario_administrador.telefono = "3101234567"
    assert enlace_whatsapp_alerta(vencimiento, usuario_administrador, hoy=HOY).startswith(
        "https://wa.me/573101234567?text="
    )
    usuario_administrador.telefono = "6011234"
    assert enlace_whatsapp_alerta(vencimiento, usuario_administrador, hoy=HOY) is None


# ---------------------------------------------------------------------------
# Avisos dentro del sistema
# ---------------------------------------------------------------------------


def test_los_avisos_son_solo_del_responsable(vencimiento, usuario_administrador, usuario_senior):
    _alerta(vencimiento, canal=ConfiguracionAlerta.NOTIFICACION)
    assert len(selectores.avisos_para_usuario(usuario_administrador, hoy=HOY)) == 1
    assert selectores.avisos_para_usuario(usuario_senior, hoy=HOY) == []


def test_un_aviso_por_vencimiento_aunque_tenga_varias_alertas(vencimiento, usuario_administrador):
    _alerta(vencimiento, dias=3)
    _alerta(vencimiento, dias=5, canal=ConfiguracionAlerta.WHATSAPP)

    avisos = selectores.avisos_para_usuario(usuario_administrador, hoy=HOY)

    assert len(avisos) == 1
    assert avisos[0]["dias"] == 3
    assert avisos[0]["whatsapp"] is True


def test_no_hay_avisos_antes_de_la_fecha_ni_con_el_vencimiento_presentado(vencimiento, usuario_administrador):
    _alerta(vencimiento)
    assert selectores.avisos_para_usuario(usuario_administrador, hoy=HOY - timedelta(days=1)) == []
    vencimiento.estado_presentacion = Vencimiento.PRESENTADA
    vencimiento.save()
    assert selectores.avisos_para_usuario(usuario_administrador, hoy=HOY) == []


# ---------------------------------------------------------------------------
# Comando y campana
# ---------------------------------------------------------------------------


def test_el_comando_procesa_las_alertas(vencimiento):
    _alerta(vencimiento)
    salida = StringIO()
    with mock.patch("django.utils.timezone.localdate", return_value=HOY):
        call_command("procesar_alertas", stdout=salida)

    assert "Correos enviados: 1" in salida.getvalue()
    assert len(mail.outbox) == 1


def test_la_campana_muestra_los_avisos_del_usuario(client, vencimiento, usuario_administrador):
    _alerta(vencimiento)
    client.force_login(usuario_administrador)
    with mock.patch("django.utils.timezone.localdate", return_value=HOY):
        respuesta = client.get(reverse("seguridad:panel"))

    assert respuesta.context["total_avisos_vencimientos"] == 1
    contenido = respuesta.content.decode()
    assert "campanaAvisos" in contenido
    assert "IVA bimestral" in contenido and "Vence en 3 días" in contenido


def test_la_campana_no_aparece_sin_sesion(client):
    contenido = client.get(reverse("seguridad:iniciar_sesion")).content.decode()
    assert "campanaAvisos" not in contenido
