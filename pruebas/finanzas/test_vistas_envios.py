"""Pruebas de vistas, permisos y seguridad de los envíos del módulo 6 (HU045-HU047 y programación)."""

from datetime import timedelta

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from aplicaciones.comunicaciones.models import Comunicacion
from aplicaciones.finanzas import envios, servicios
from aplicaciones.finanzas.models import CORREO, WHATSAPP, ConfiguracionCobro, EnvioProgramado

pytestmark = pytest.mark.django_db

URLS_ADMIN = [
    "finanzas:envio_masivo",
    "finanzas:envio_masivo_resumen",
    "finanzas:bandeja_whatsapp",
    "finanzas:programados",
    "finanzas:configuracion",
]


def _manana():
    return (timezone.localtime() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")


# ---------------------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nombre_url", URLS_ADMIN)
def test_pantallas_de_envio_requieren_sesion(client, nombre_url):
    respuesta = client.get(reverse(nombre_url))
    assert respuesta.status_code == 302


@pytest.mark.parametrize("usuario_fixture", ["usuario_senior", "usuario_junior"])
@pytest.mark.parametrize("nombre_url", URLS_ADMIN)
def test_solo_administrador_accede_a_envios(client, request, usuario_fixture, nombre_url):
    client.force_login(request.getfixturevalue(usuario_fixture))
    assert client.get(reverse(nombre_url)).status_code == 403


@pytest.mark.parametrize("usuario_fixture", ["usuario_senior", "usuario_junior"])
def test_senior_y_junior_no_envian_ni_ejecutan_el_proceso(
    client, request, usuario_fixture, cuenta_cliente_junior
):
    client.force_login(request.getfixturevalue(usuario_fixture))
    enviar = client.post(
        reverse("finanzas:enviar", args=[cuenta_cliente_junior.pk]),
        {"tipo": EnvioProgramado.CUENTA_COBRO, "canal": CORREO, "modo": "ahora"},
    )
    assert enviar.status_code == 403
    assert client.post(reverse("finanzas:ejecutar_proceso")).status_code == 403
    assert not mail.outbox


def test_junior_ve_el_historial_de_envios_de_su_cliente_sin_acciones(
    client, usuario_junior, usuario_administrador, cuenta_cliente_junior
):
    servicios.enviar_ahora(
        [cuenta_cliente_junior], EnvioProgramado.CUENTA_COBRO, WHATSAPP, usuario_administrador
    )
    client.force_login(usuario_junior)
    contenido = client.get(reverse("finanzas:detalle", args=[cuenta_cliente_junior.pk])).content.decode()
    assert "Historial de envíos" in contenido
    assert "Pendiente WhatsApp" in contenido
    assert "Abrir WhatsApp" not in contenido
    assert reverse("finanzas:enviar", args=[cuenta_cliente_junior.pk]) not in contenido


# ---------------------------------------------------------------------------
# Envío individual (HU045)
# ---------------------------------------------------------------------------


def test_enviar_cuenta_por_correo_desde_el_detalle(client, usuario_administrador, cuenta_cliente):
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("finanzas:enviar", args=[cuenta_cliente.pk]),
        {"tipo": EnvioProgramado.CUENTA_COBRO, "canal": CORREO, "modo": "ahora"},
        follow=True,
    )
    assert len(mail.outbox) == 1
    assert "enviada por correo" in respuesta.content.decode()


def test_programar_envio_desde_el_detalle(client, usuario_administrador, cuenta_cliente):
    client.force_login(usuario_administrador)
    client.post(
        reverse("finanzas:enviar", args=[cuenta_cliente.pk]),
        {
            "tipo": EnvioProgramado.RECORDATORIO,
            "canal": "Ambos",
            "modo": "programar",
            "fecha_programada": _manana(),
        },
    )
    assert EnvioProgramado.objects.filter(estado=EnvioProgramado.PROGRAMADO).count() == 2
    assert not mail.outbox


def test_programar_en_el_pasado_es_rechazado(client, usuario_administrador, cuenta_cliente):
    client.force_login(usuario_administrador)
    ayer = (timezone.localtime() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
    respuesta = client.post(
        reverse("finanzas:enviar", args=[cuenta_cliente.pk]),
        {
            "tipo": EnvioProgramado.CUENTA_COBRO,
            "canal": CORREO,
            "modo": "programar",
            "fecha_programada": ayer,
        },
        follow=True,
    )
    assert not EnvioProgramado.objects.exists()
    assert "debe ser futura" in respuesta.content.decode()


def test_abrir_whatsapp_registra_y_redirige_a_wa_me(client, usuario_administrador, cuenta_cliente):
    [envio] = servicios.enviar_ahora(
        [cuenta_cliente], EnvioProgramado.CUENTA_COBRO, WHATSAPP, usuario_administrador
    )
    client.force_login(usuario_administrador)
    respuesta = client.post(reverse("finanzas:abrir_whatsapp", args=[envio.pk]))
    assert respuesta.status_code == 302
    assert respuesta.url.startswith("https://wa.me/573101234567")
    assert Comunicacion.objects.get().canal == Comunicacion.WHATSAPP


def test_abrir_whatsapp_por_get_no_esta_permitido(client, usuario_administrador, cuenta_cliente):
    [envio] = servicios.enviar_ahora(
        [cuenta_cliente], EnvioProgramado.CUENTA_COBRO, WHATSAPP, usuario_administrador
    )
    client.force_login(usuario_administrador)
    assert client.get(reverse("finanzas:abrir_whatsapp", args=[envio.pk])).status_code == 405
    assert not Comunicacion.objects.exists()


def test_siguiente_externo_se_ignora(client, usuario_administrador, cuenta_cliente):
    [envio] = servicios.programar_envio(
        cuenta_cliente, EnvioProgramado.CUENTA_COBRO, CORREO, timezone.now() + timedelta(days=1)
    )
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("finanzas:cancelar_envio", args=[envio.pk]), {"siguiente": "https://sitio-malicioso.com/"}
    )
    assert respuesta.url == reverse("finanzas:programados")


def test_reintentar_desde_la_vista(client, usuario_administrador, cliente, generar_cuenta):
    cliente.correo_cliente = ""
    cliente.save()
    cuenta = generar_cuenta(cliente)
    [envio] = servicios.enviar_ahora([cuenta], EnvioProgramado.CUENTA_COBRO, CORREO, usuario_administrador)
    cliente.correo_cliente = "nuevo@cliente.co"
    cliente.save()
    client.force_login(usuario_administrador)
    client.post(reverse("finanzas:reintentar", args=[envio.pk]))
    envio.refresh_from_db()
    assert envio.estado == EnvioProgramado.ENVIADO
    assert mail.outbox[0].to == ["nuevo@cliente.co"]


# ---------------------------------------------------------------------------
# Envío masivo (HU046, HU047)
# ---------------------------------------------------------------------------


def test_envio_masivo_pide_confirmacion_antes_de_enviar(
    client, usuario_administrador, cuenta_cliente, cuenta_cliente_junior
):
    client.force_login(usuario_administrador)
    listado = client.get(reverse("finanzas:envio_masivo"))
    assert set(listado.context["candidatas"]) == {cuenta_cliente, cuenta_cliente_junior}

    datos = {
        "tipo": EnvioProgramado.CUENTA_COBRO,
        "canal": CORREO,
        "modo": "ahora",
        "cuentas": [cuenta_cliente.pk, cuenta_cliente_junior.pk],
    }
    confirmacion = client.post(reverse("finanzas:envio_masivo"), datos)
    assert confirmacion.status_code == 200
    assert "Confirmar envío" in confirmacion.content.decode()
    assert not mail.outbox

    respuesta = client.post(reverse("finanzas:envio_masivo"), {**datos, "confirmar": "1"})
    assert respuesta.url == reverse("finanzas:envio_masivo_resumen")
    resumen = client.get(respuesta.url)
    assert resumen.context["conteo"]["enviados"] == 1  # el cliente del Junior no tiene correo
    assert resumen.context["conteo"]["fallidos"] == 1
    assert "no tiene correo" in resumen.content.decode()


def test_envio_masivo_exige_seleccion(client, usuario_administrador, cuenta_cliente):
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("finanzas:envio_masivo"),
        {"tipo": EnvioProgramado.CUENTA_COBRO, "canal": CORREO, "modo": "ahora"},
    )
    assert "Seleccione al menos una cuenta" in respuesta.content.decode()


def test_envio_masivo_rechaza_cuentas_fuera_del_listado(client, usuario_administrador, cuenta_cliente):
    servicios.enviar_ahora([cuenta_cliente], EnvioProgramado.CUENTA_COBRO, CORREO, usuario_administrador)
    mail.outbox.clear()
    client.force_login(usuario_administrador)
    # La cuenta ya se envió: no es candidata al envío masivo de cuentas, aunque se fuerce su id.
    respuesta = client.post(
        reverse("finanzas:envio_masivo"),
        {
            "tipo": EnvioProgramado.CUENTA_COBRO,
            "canal": CORREO,
            "modo": "ahora",
            "cuentas": [cuenta_cliente.pk],
            "confirmar": "1",
        },
    )
    assert respuesta.status_code == 200
    assert not mail.outbox


def test_recordatorios_masivos_listan_solo_cuentas_con_saldo(
    client, usuario_administrador, cuenta_cliente, cuenta_cliente_junior
):
    cuenta_cliente.abonos.create(
        monto=cuenta_cliente.valor_total,
        responsable=usuario_administrador,
        saldo_anterior=cuenta_cliente.valor_total,
        saldo_resultante=0,
    )
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("finanzas:envio_masivo"), {"tipo": EnvioProgramado.RECORDATORIO})
    assert respuesta.context["candidatas"] == [cuenta_cliente_junior]


def test_envio_masivo_programado(client, usuario_administrador, cuenta_cliente):
    client.force_login(usuario_administrador)
    client.post(
        reverse("finanzas:envio_masivo"),
        {
            "tipo": EnvioProgramado.CUENTA_COBRO,
            "canal": WHATSAPP,
            "modo": "programar",
            "fecha_programada": _manana(),
            "cuentas": [cuenta_cliente.pk],
            "confirmar": "1",
        },
    )
    assert EnvioProgramado.objects.get().estado == EnvioProgramado.PROGRAMADO


# ---------------------------------------------------------------------------
# Bandeja, programados, configuración y PDF público
# ---------------------------------------------------------------------------


def test_bandeja_muestra_whatsapp_pendientes(client, usuario_administrador, cuenta_cliente):
    servicios.enviar_ahora([cuenta_cliente], EnvioProgramado.RECORDATORIO, WHATSAPP, usuario_administrador)
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("finanzas:bandeja_whatsapp"))
    assert len(respuesta.context["pendientes"]) == 1
    assert "Abrir WhatsApp" in respuesta.content.decode()
    historico = client.get(reverse("finanzas:historico"))
    assert historico.context["pendientes_whatsapp"] == 1


def test_listado_de_programados_filtra_por_estado(client, usuario_administrador, cuenta_cliente):
    servicios.programar_envio(
        cuenta_cliente, EnvioProgramado.CUENTA_COBRO, "Ambos", timezone.now() + timedelta(days=1)
    )
    client.force_login(usuario_administrador)
    assert len(client.get(reverse("finanzas:programados")).context["envios"]) == 2
    filtrado = client.get(reverse("finanzas:programados"), {"estado": EnvioProgramado.ENVIADO})
    assert len(filtrado.context["envios"]) == 0


def test_configuracion_guarda_y_valida(client, usuario_administrador):
    client.force_login(usuario_administrador)
    datos = {
        "cobro_automatico_activo": "on",
        "dia_generacion": "31",
        "dias_plazo_pago": "10",
        "canal_cobro": CORREO,
        "dias_antes_vencimiento": "3",
        "frecuencia_mora_dias": "7",
        "canal_recordatorio": CORREO,
    }
    invalida = client.post(reverse("finanzas:configuracion"), datos)
    assert "entre 1 y 28" in invalida.content.decode()
    client.post(reverse("finanzas:configuracion"), {**datos, "dia_generacion": "5"})
    configuracion = ConfiguracionCobro.obtener()
    assert configuracion.cobro_automatico_activo
    assert configuracion.dia_generacion == 5


def test_ejecutar_ahora_muestra_resumen(client, usuario_administrador):
    client.force_login(usuario_administrador)
    respuesta = client.post(reverse("finanzas:ejecutar_proceso"), follow=True)
    assert "Proceso ejecutado" in respuesta.content.decode()
    assert ConfiguracionCobro.obtener().ultima_ejecucion is not None


def test_pdf_publico_con_token_valido_sin_sesion(client, cuenta_cliente):
    respuesta = client.get(reverse("finanzas:pdf_publico", args=[envios.token_pdf_publico(cuenta_cliente)]))
    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == "application/pdf"
    assert "inline" in respuesta["Content-Disposition"]


@pytest.mark.parametrize("token", ["1:abc:def", "no-es-un-token"])
def test_pdf_publico_con_token_invalido_es_404(client, cuenta_cliente, token):
    assert client.get(reverse("finanzas:pdf_publico", args=[token])).status_code == 404


def test_pdf_publico_no_permite_adivinar_otra_cuenta(client, cuenta_cliente, cuenta_cliente_junior):
    token = envios.token_pdf_publico(cuenta_cliente)
    alterado = token.replace(f"{cuenta_cliente.pk}:", f"{cuenta_cliente_junior.pk}:", 1)
    assert client.get(reverse("finanzas:pdf_publico", args=[alterado])).status_code == 404


# ---------------------------------------------------------------------------
# Envío masivo con una fecha distinta por cliente
# ---------------------------------------------------------------------------


def _en_dias(dias, hora=9):
    fecha = timezone.localtime() + timedelta(days=dias)
    return fecha.replace(hour=hora, minute=0).strftime("%Y-%m-%dT%H:%M")


def test_envio_masivo_programa_cada_cliente_en_su_fecha(
    client, usuario_administrador, cuenta_cliente, cuenta_cliente_junior
):
    client.force_login(usuario_administrador)
    datos = {
        "tipo": EnvioProgramado.CUENTA_COBRO,
        "canal": CORREO,
        "modo": "programar",
        "cuentas": [cuenta_cliente.pk, cuenta_cliente_junior.pk],
        f"fecha_{cuenta_cliente.pk}": _en_dias(2),
        f"fecha_{cuenta_cliente_junior.pk}": _en_dias(5),
    }
    confirmacion = client.post(reverse("finanzas:envio_masivo"), datos)
    assert "en la fecha indicada para cada cliente" in confirmacion.content.decode()
    assert confirmacion.context["fecha_unica"] is None

    client.post(reverse("finanzas:envio_masivo"), {**datos, "confirmar": "1"})
    fechas = {
        envio.cuenta_cobro_id: timezone.localtime(envio.fecha_programada).strftime("%Y-%m-%dT%H:%M")
        for envio in EnvioProgramado.objects.all()
    }
    assert fechas == {cuenta_cliente.pk: _en_dias(2), cuenta_cliente_junior.pk: _en_dias(5)}
    assert not mail.outbox


def test_envio_masivo_usa_la_fecha_general_si_la_cuenta_no_trae_la_suya(
    client, usuario_administrador, cuenta_cliente, cuenta_cliente_junior
):
    client.force_login(usuario_administrador)
    client.post(
        reverse("finanzas:envio_masivo"),
        {
            "tipo": EnvioProgramado.CUENTA_COBRO,
            "canal": CORREO,
            "modo": "programar",
            "fecha_programada": _en_dias(3),
            "cuentas": [cuenta_cliente.pk, cuenta_cliente_junior.pk],
            f"fecha_{cuenta_cliente_junior.pk}": _en_dias(7),
            "confirmar": "1",
        },
    )
    propia = EnvioProgramado.objects.get(cuenta_cobro=cuenta_cliente_junior)
    general = EnvioProgramado.objects.get(cuenta_cobro=cuenta_cliente)
    assert timezone.localtime(propia.fecha_programada).strftime("%Y-%m-%dT%H:%M") == _en_dias(7)
    assert timezone.localtime(general.fecha_programada).strftime("%Y-%m-%dT%H:%M") == _en_dias(3)


@pytest.mark.parametrize("fecha_propia", ["", "2020-01-01T08:00", "no-es-fecha"])
def test_envio_masivo_exige_fecha_futura_por_cuenta(
    client, usuario_administrador, cuenta_cliente, fecha_propia
):
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("finanzas:envio_masivo"),
        {
            "tipo": EnvioProgramado.CUENTA_COBRO,
            "canal": CORREO,
            "modo": "programar",
            "cuentas": [cuenta_cliente.pk],
            f"fecha_{cuenta_cliente.pk}": fecha_propia,
            "confirmar": "1",
        },
    )
    assert respuesta.status_code == 200
    assert "Revise las fechas de envío" in respuesta.content.decode()
    assert respuesta.context["filas"][0]["error_fecha"]
    assert respuesta.context["filas"][0]["seleccionada"]
    assert not EnvioProgramado.objects.exists()


def test_envio_masivo_puede_incluir_cuentas_ya_enviadas(client, usuario_administrador, cuenta_cliente):
    servicios.enviar_ahora([cuenta_cliente], EnvioProgramado.CUENTA_COBRO, CORREO, usuario_administrador)
    mail.outbox.clear()
    client.force_login(usuario_administrador)
    assert client.get(reverse("finanzas:envio_masivo")).context["candidatas"] == []
    respuesta = client.get(reverse("finanzas:envio_masivo"), {"incluir_enviadas": "1"})
    assert respuesta.context["candidatas"] == [cuenta_cliente]

    client.post(
        reverse("finanzas:envio_masivo"),
        {
            "tipo": EnvioProgramado.CUENTA_COBRO,
            "canal": CORREO,
            "modo": "ahora",
            "incluir_enviadas": "1",
            "cuentas": [cuenta_cliente.pk],
            "confirmar": "1",
        },
    )
    assert len(mail.outbox) == 1
