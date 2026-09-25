"""Pruebas de los envíos del módulo 6: correo, WhatsApp, enlace público y reintentos."""

from datetime import timedelta
from decimal import Decimal
from urllib.parse import unquote

import pytest
from django.core import mail
from django.utils import timezone

from aplicaciones.comunicaciones.models import Comunicacion
from aplicaciones.finanzas import envios, servicios
from aplicaciones.finanzas.models import AMBOS, CORREO, WHATSAPP, CuentaCobro, EnvioProgramado

pytestmark = pytest.mark.django_db


@pytest.fixture
def falla_smtp(monkeypatch):
    """Simula que el servidor de correo rechaza el envío."""

    def rechazar(*args, **kwargs):
        raise OSError("Conexión rechazada por el servidor SMTP")

    monkeypatch.setattr(envios.EmailMessage, "send", rechazar)


# ---------------------------------------------------------------------------
# Número y enlace de WhatsApp
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("contacto", "esperado"),
    [
        ("3101234567", "573101234567"),
        ("310 123 4567", "573101234567"),
        ("+57 310-123-4567", "573101234567"),
        ("6015551234", None),
        ("", None),
    ],
)
def test_numero_whatsapp(cliente, contacto, esperado):
    cliente.informacion_contacto = contacto
    assert envios.numero_whatsapp(cliente) == esperado


def test_enlace_whatsapp_incluye_saldo_vencimiento_banco_y_pdf(cliente, generar_cuenta, cuenta_bancaria):
    cuenta = generar_cuenta(cliente, cuenta_bancaria=cuenta_bancaria)
    enlace = envios.enlace_whatsapp(cuenta, EnvioProgramado.RECORDATORIO)
    assert enlace.startswith("https://wa.me/573101234567?text=")
    texto = unquote(enlace)
    assert "$ 1.000.000" in texto
    assert "Bancolombia" in texto
    assert "/cuenta-cobro/" in texto


def test_enlace_whatsapp_sin_celular_devuelve_none(cliente, generar_cuenta):
    cliente.informacion_contacto = ""
    cliente.save()
    assert envios.enlace_whatsapp(generar_cuenta(cliente), EnvioProgramado.CUENTA_COBRO) is None


def test_token_pdf_publico_valido_alterado_y_vencido(cuenta_cliente, monkeypatch):
    token = envios.token_pdf_publico(cuenta_cliente)
    assert envios.cuenta_desde_token(token) == cuenta_cliente
    assert envios.cuenta_desde_token(token + "x") is None
    monkeypatch.setattr(envios, "VIGENCIA_ENLACE_PDF", -1)
    assert envios.cuenta_desde_token(token) is None


# ---------------------------------------------------------------------------
# Envío por correo
# ---------------------------------------------------------------------------


def test_enviar_cuenta_por_correo_adjunta_pdf_y_registra(cuenta_cliente, usuario_administrador):
    [envio] = servicios.enviar_ahora(
        [cuenta_cliente], EnvioProgramado.CUENTA_COBRO, CORREO, usuario_administrador
    )

    assert envio.estado == EnvioProgramado.ENVIADO
    assert len(mail.outbox) == 1
    correo = mail.outbox[0]
    assert correo.to == ["gerencia@larebaja.co"]
    assert f"Cuenta de cobro No. {cuenta_cliente.pk}" in correo.subject
    assert correo.attachments[0][0] == f"cuenta_cobro_{cuenta_cliente.pk}.pdf"
    assert correo.attachments[0][1].startswith(b"%PDF-")

    comunicacion = Comunicacion.objects.get()
    assert comunicacion.canal == Comunicacion.CORREO
    assert comunicacion.estado_envio == Comunicacion.EXITO
    assert comunicacion.usuario == usuario_administrador
    assert comunicacion.modulo_origen == "Honorarios"
    cuenta_cliente.refresh_from_db()
    assert cuenta_cliente.estado_envio == CuentaCobro.ENVIADA


def test_recordatorio_por_correo_no_adjunta_pero_menciona_saldo(cuenta_cliente, usuario_administrador):
    servicios.enviar_ahora([cuenta_cliente], EnvioProgramado.RECORDATORIO, CORREO, usuario_administrador)
    correo = mail.outbox[0]
    assert "Recordatorio de pago" in correo.subject
    assert "$ 1.000.000" in correo.body
    cuenta_cliente.refresh_from_db()
    assert (
        cuenta_cliente.estado_envio == CuentaCobro.PENDIENTE
    )  # un recordatorio no cambia el envío de la cuenta


def test_correo_sin_destinatario_queda_fallido(cliente, generar_cuenta, usuario_administrador):
    cliente.correo_cliente = ""
    cliente.save()
    cuenta = generar_cuenta(cliente)
    [envio] = servicios.enviar_ahora([cuenta], EnvioProgramado.CUENTA_COBRO, CORREO, usuario_administrador)
    assert envio.estado == EnvioProgramado.FALLIDO
    assert "no tiene correo" in envio.detalle_error
    cuenta.refresh_from_db()
    assert cuenta.estado_envio == CuentaCobro.FALLIDA


def test_fallo_smtp_y_reintento_exitoso(cuenta_cliente, usuario_administrador, falla_smtp, monkeypatch):
    [envio] = servicios.enviar_ahora(
        [cuenta_cliente], EnvioProgramado.CUENTA_COBRO, CORREO, usuario_administrador
    )
    assert envio.estado == EnvioProgramado.FALLIDO
    assert "SMTP" in envio.detalle_error
    assert envio.comunicacion.estado_envio == Comunicacion.FALLO

    monkeypatch.undo()
    servicios.reintentar_envio(envio, usuario_administrador)
    envio.refresh_from_db()
    assert envio.estado == EnvioProgramado.ENVIADO
    assert envio.comunicacion.numero_reintentos == 1
    assert len(mail.outbox) == 1


def test_solo_se_reintentan_los_fallidos(cuenta_cliente, usuario_administrador):
    [envio] = servicios.enviar_ahora(
        [cuenta_cliente], EnvioProgramado.CUENTA_COBRO, CORREO, usuario_administrador
    )
    with pytest.raises(ValueError):
        servicios.reintentar_envio(envio, usuario_administrador)


# ---------------------------------------------------------------------------
# WhatsApp: bandeja y confirmación
# ---------------------------------------------------------------------------


def test_whatsapp_queda_pendiente_y_se_confirma_al_abrir(cuenta_cliente, usuario_administrador):
    [envio] = servicios.enviar_ahora(
        [cuenta_cliente], EnvioProgramado.CUENTA_COBRO, WHATSAPP, usuario_administrador
    )
    assert envio.estado == EnvioProgramado.PENDIENTE_WHATSAPP
    assert not Comunicacion.objects.exists()

    enlace = servicios.confirmar_whatsapp(envio, usuario_administrador)
    assert enlace.startswith("https://wa.me/")
    envio.refresh_from_db()
    assert envio.estado == EnvioProgramado.ENVIADO
    assert Comunicacion.objects.get().canal == Comunicacion.WHATSAPP
    with pytest.raises(ValueError):
        servicios.confirmar_whatsapp(envio, usuario_administrador)


def test_confirmar_whatsapp_sin_celular_no_registra(cliente, generar_cuenta, usuario_administrador):
    cliente.informacion_contacto = "sin número"
    cliente.save()
    [envio] = servicios.enviar_ahora(
        [generar_cuenta(cliente)], EnvioProgramado.CUENTA_COBRO, WHATSAPP, usuario_administrador
    )
    with pytest.raises(ValueError):
        servicios.confirmar_whatsapp(envio, usuario_administrador)
    assert not Comunicacion.objects.exists()


def test_canal_ambos_crea_correo_y_whatsapp(cuenta_cliente, usuario_administrador):
    procesados = servicios.enviar_ahora(
        [cuenta_cliente], EnvioProgramado.CUENTA_COBRO, AMBOS, usuario_administrador
    )
    assert {envio.canal: envio.estado for envio in procesados} == {
        CORREO: EnvioProgramado.ENVIADO,
        WHATSAPP: EnvioProgramado.PENDIENTE_WHATSAPP,
    }


# ---------------------------------------------------------------------------
# Programación y cancelación
# ---------------------------------------------------------------------------


def test_envio_programado_se_despacha_solo_al_llegar_la_hora(cuenta_cliente, usuario_administrador):
    ahora = timezone.now()
    servicios.programar_envio(
        cuenta_cliente,
        EnvioProgramado.CUENTA_COBRO,
        CORREO,
        ahora + timedelta(hours=1),
        usuario_administrador,
    )
    assert servicios.despachar_programados(ahora) == []
    [envio] = servicios.despachar_programados(ahora + timedelta(hours=2))
    assert envio.estado == EnvioProgramado.ENVIADO
    assert envio.comunicacion.tipo == Comunicacion.AUTOMATICA
    assert len(mail.outbox) == 1


def test_cancelar_envio_programado(cuenta_cliente, usuario_administrador):
    [envio] = servicios.programar_envio(
        cuenta_cliente, EnvioProgramado.CUENTA_COBRO, CORREO, timezone.now() + timedelta(days=1)
    )
    servicios.cancelar_envio(envio)
    assert envio.estado == EnvioProgramado.CANCELADO
    with pytest.raises(ValueError):
        servicios.cancelar_envio(envio)
    assert servicios.despachar_programados(timezone.now() + timedelta(days=2)) == []


def test_mensaje_de_correo_no_escapa_html_ni_ejecuta_nada(cliente, generar_cuenta, usuario_administrador):
    cliente.nombre_razon_social = "Tienda <b>& Cía</b>"
    cliente.save()
    servicios.enviar_ahora(
        [generar_cuenta(cliente)], EnvioProgramado.CUENTA_COBRO, CORREO, usuario_administrador
    )
    # Texto plano: se ve tal cual lo escribió el usuario, sin entidades HTML.
    assert "Tienda <b>& Cía</b>" in mail.outbox[0].body
    assert mail.outbox[0].content_subtype == "plain"


def test_saldo_del_mensaje_descuenta_abonos(cuenta_cliente, usuario_administrador):
    cuenta_cliente.abonos.create(
        monto=Decimal("400000"),
        responsable=usuario_administrador,
        saldo_anterior=Decimal("1000000"),
        saldo_resultante=Decimal("600000"),
    )
    servicios.enviar_ahora([cuenta_cliente], EnvioProgramado.RECORDATORIO, CORREO, usuario_administrador)
    assert "$ 600.000" in mail.outbox[0].body
