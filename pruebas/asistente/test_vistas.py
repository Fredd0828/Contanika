"""Pruebas de las vistas del asistente: acceso por rol y preguntas sugeridas."""

from datetime import date

import pytest
from django.urls import NoReverseMatch, reverse

from aplicaciones.seguridad import guias
from aplicaciones.seguridad.models import Modulo

from .conftest import crear_vencimiento, inhabilitar

pytestmark = pytest.mark.django_db

URL_INICIO = reverse("asistente:inicio")


def _consultar(slug):
    return reverse("asistente:consultar", args=[slug])


# ---------------------------------------------------------------------------
# Página del asistente
# ---------------------------------------------------------------------------


def test_el_asistente_exige_iniciar_sesion(client):
    respuesta = client.get(URL_INICIO)

    assert respuesta.status_code == 302
    assert reverse("seguridad:iniciar_sesion") in respuesta.url


def test_el_administrador_puede_apagar_el_asistente_para_un_rol(client, usuario_junior, rol_junior):
    inhabilitar(rol_junior, Modulo.SEC_ASISTENTE)
    client.force_login(usuario_junior)

    assert client.get(URL_INICIO).status_code == 403
    assert client.post(_consultar("vencimientos-semana")).status_code == 403
    assert URL_INICIO not in client.get(reverse("seguridad:ayuda")).content.decode()


def test_la_pagina_muestra_las_preguntas_de_los_modulos_habilitados(
    client, usuario_junior, rol_junior, cliente
):
    inhabilitar(rol_junior, Modulo.MOD06_FINANZAS)
    client.force_login(usuario_junior)

    contenido = client.get(URL_INICIO).content.decode()

    assert "¿Qué vence esta semana?" in contenido
    assert "¿Qué clientes tienen saldo pendiente?" not in contenido
    assert 'id="asCliente-vencimientos-cliente"' in contenido
    assert "Comercializadora La Rebaja SAS · 900123456" in contenido
    assert all(faq.pregunta in contenido for faq in guias.PREGUNTAS_FRECUENTES)
    assert URL_INICIO in contenido  # enlace del menú lateral


def test_el_asistente_no_tiene_chat_libre(client, usuario_administrador):
    """Solo responde preguntas sugeridas: no hay campo para escribir ni ruta de chat."""
    client.force_login(usuario_administrador)

    contenido = client.get(URL_INICIO).content.decode()

    assert "<textarea" not in contenido
    with pytest.raises(NoReverseMatch):
        reverse("asistente:preguntar")
    assert client.post("/asistente/preguntar/", {"pregunta": "Hola"}).status_code == 404


# ---------------------------------------------------------------------------
# Preguntas sugeridas
# ---------------------------------------------------------------------------


def test_consultar_devuelve_el_fragmento_con_la_respuesta(client, usuario_administrador):
    client.force_login(usuario_administrador)

    respuesta = client.post(_consultar("hallazgos-abiertos"))

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert contenido.strip().startswith('<div class="as-msg as-msg-bot as-msg-datos">')
    assert "Hallazgos sin cerrar: 0" in contenido
    assert "No hay hallazgos abiertos." in contenido
    assert reverse("hallazgos:lista") in contenido


def test_consultar_por_cliente(client, usuario_administrador, cliente):
    client.force_login(usuario_administrador)

    respuesta = client.post(_consultar("vencimientos-cliente"), {"cliente": cliente.pk})

    assert respuesta.status_code == 200
    assert "Vencimientos sin presentar de Comercializadora La Rebaja SAS: 0" in respuesta.content.decode()


def test_la_respuesta_muestra_las_filas_con_sus_columnas(client, usuario_administrador, cliente):
    crear_vencimiento(cliente, date(2026, 11, 20), tipo="Retención en la fuente")
    client.force_login(usuario_administrador)

    contenido = client.post(_consultar("vencimientos-cliente"), {"cliente": cliente.pk}).content.decode()

    assert "Vencimientos sin presentar de Comercializadora La Rebaja SAS: 1" in contenido
    assert "Retención en la fuente" in contenido
    assert "20/11/2026" in contenido


def test_consultar_sin_cliente_valido_responde_400(client, usuario_senior, cliente):
    client.force_login(usuario_senior)

    respuesta = client.post(_consultar("saldo-cliente"), {"cliente": cliente.pk})  # cliente ajeno

    assert respuesta.status_code == 400
    assert "Elija un cliente de la lista" in respuesta.content.decode()


def test_consultar_una_pregunta_inhabilitada_o_inexistente_responde_404(client, usuario_junior, rol_junior):
    inhabilitar(rol_junior, Modulo.MOD06_FINANZAS)
    client.force_login(usuario_junior)

    assert client.post(_consultar("cartera-pendiente")).status_code == 404
    assert client.post(_consultar("no-existe")).status_code == 404


def test_consultar_solo_acepta_post(client, usuario_administrador):
    client.force_login(usuario_administrador)

    assert client.get(_consultar("vencimientos-semana")).status_code == 405


def test_consultar_exige_el_token_csrf(usuario_administrador):
    from django.test import Client

    cliente_http = Client(enforce_csrf_checks=True)
    cliente_http.force_login(usuario_administrador)

    assert cliente_http.post(_consultar("vencimientos-semana")).status_code == 403


# ---------------------------------------------------------------------------
# Ayuda
# ---------------------------------------------------------------------------


def test_la_ayuda_muestra_las_preguntas_frecuentes_del_catalogo(client, usuario_administrador):
    client.force_login(usuario_administrador)

    contenido = client.get(reverse("seguridad:ayuda")).content.decode()

    assert all(faq.pregunta in contenido for faq in guias.PREGUNTAS_FRECUENTES)
    assert reverse("seguridad:guia", args=["consultar-asistente"]) in contenido
