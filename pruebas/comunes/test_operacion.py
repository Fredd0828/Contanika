"""Pruebas de las rutas de monitoreo y de la elección de la configuración."""

from unittest import mock

import pytest
from django.db import Error as ErrorBaseDatos
from django.test import override_settings
from django.urls import reverse

from gestionar import modulo_de_configuracion

pytestmark = pytest.mark.django_db


def test_salud_informa_que_la_aplicacion_y_la_base_responden(client):
    respuesta = client.get(reverse("salud"))
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok", "base_datos": "ok"}


def test_salud_responde_503_si_la_base_no_contesta(client):
    with mock.patch("aplicaciones.comunes.vistas.connection.cursor", side_effect=ErrorBaseDatos("caída")):
        respuesta = client.get(reverse("salud"))
    assert respuesta.status_code == 503
    assert respuesta.json() == {"estado": "error", "base_datos": "error"}


def test_salud_no_revela_el_detalle_del_error(client):
    with mock.patch(
        "aplicaciones.comunes.vistas.connection.cursor",
        side_effect=ErrorBaseDatos("clave-secreta-del-servidor"),
    ):
        respuesta = client.get(reverse("salud"))
    assert "clave-secreta" not in respuesta.content.decode()


@override_settings(VERSION_APLICACION="9.9.9")
def test_version_devuelve_la_version_configurada(client):
    respuesta = client.get(reverse("version"))
    assert respuesta.status_code == 200
    assert respuesta.json() == {"version": "9.9.9"}


@pytest.mark.parametrize("nombre", ["salud", "version"])
def test_rutas_de_monitoreo_no_exigen_sesion_ni_aceptan_post(client, nombre):
    assert client.get(reverse(nombre)).status_code == 200
    assert client.post(reverse(nombre)).status_code == 405


@pytest.mark.parametrize("nombre", ["salud", "version"])
@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
def test_rutas_de_monitoreo_limitan_las_peticiones(client, nombre):
    respuestas = [client.get(reverse(nombre)).status_code for _ in range(61)]
    assert respuestas[0] == 200
    assert respuestas[-1] == 429


@pytest.mark.parametrize(
    ("entorno", "esperado"),
    [
        ("produccion", "config.settings.produccion"),
        ("PRODUCCION", "config.settings.produccion"),
        (" produccion ", "config.settings.produccion"),
        ("local", "config.settings.local"),
        ("", "config.settings.local"),
        ("otro", "config.settings.local"),
    ],
)
def test_entorno_elige_el_modulo_de_configuracion(entorno, esperado):
    assert modulo_de_configuracion(entorno) == esperado
