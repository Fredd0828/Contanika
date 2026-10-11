"""
Pruebas de seguridad transversales (Fase 4): matriz rol × módulo × acción.

Recorren **todas** las rutas del sistema, tomadas del mismo recorrido que
genera el mapa de navegación, así una ruta nueva queda cubierta sin escribir
su prueba. Los controles se evalúan antes de buscar el registro, por eso las
rutas con parámetros se prueban con identificadores de relleno.
"""

import re

import pytest
from django.test import Client
from django.urls import reverse

from aplicaciones.seguridad.management.commands.generar_mapa_navegacion import recorrer_rutas
from aplicaciones.seguridad.models import Modulo, PermisoRolModulo, Rol
from pruebas.conftest import CLAVE_PRUEBAS

pytestmark = pytest.mark.django_db

RUTAS = recorrer_rutas()
# Cerrar sesión no muestra ni cambia datos: sin sesión no hay nada que proteger.
PROTEGIDAS = [ruta for ruta in RUTAS if not ruta["publica"] and ruta["nombre"] != "seguridad:cerrar_sesion"]
CON_POST = [ruta for ruta in PROTEGIDAS if "POST" in ruta["metodos"]]
# Rutas que excluyen al menos a un rol (las que nombran los tres no restringen a ninguno).
CON_ROLES = [ruta for ruta in PROTEGIDAS if ruta["roles"] and len(set(ruta["roles"])) < 3]
CON_MODULO = [ruta for ruta in PROTEGIDAS if ruta["modulo"]]
FIXTURE_POR_ROL = {
    Rol.ADMINISTRADOR: "usuario_administrador",
    Rol.CONTADOR_SENIOR: "usuario_senior",
    Rol.CONTADOR_JUNIOR: "usuario_junior",
}


def _url(ruta):
    """Ruta con sus parámetros reemplazados por valores de relleno."""
    url = re.sub(r"<int:[^>]+>", "1", ruta["ruta"])
    return re.sub(r"<(?:str|slug|path):[^>]+>", "x", url)


def _pedir(cliente, ruta):
    """Usa el método principal de la ruta: GET si lo acepta; si no, POST."""
    return cliente.get(_url(ruta)) if "GET" in ruta["metodos"] else cliente.post(_url(ruta))


def _id(ruta):
    return ruta["nombre"]


def test_el_recorrido_incluye_todos_los_modulos():
    assert {ruta["modulo"] for ruta in CON_MODULO} >= {
        codigo for codigo, _ in Modulo.OPCIONES_CODIGO if codigo != Modulo.SEC_PANEL
    }
    assert len(PROTEGIDAS) > 100


@pytest.mark.parametrize("ruta", PROTEGIDAS, ids=_id)
def test_sin_sesion_toda_ruta_lleva_al_inicio_de_sesion(client, ruta):
    respuesta = _pedir(client, ruta)
    assert respuesta.status_code == 302
    assert respuesta.url.startswith(reverse("seguridad:iniciar_sesion"))


@pytest.mark.parametrize("ruta", CON_POST, ids=_id)
def test_post_sin_token_csrf_se_rechaza(usuario_administrador, ruta):
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(usuario_administrador)
    assert cliente.post(_url(ruta)).status_code == 403


@pytest.mark.parametrize("ruta", CON_ROLES, ids=_id)
def test_rol_no_permitido_recibe_403(client, request, ruta):
    """Escalada de privilegios: cada rol fuera de `roles_permitidos` queda bloqueado."""
    for rol in [rol for rol in FIXTURE_POR_ROL if rol not in ruta["roles"]]:
        client.force_login(request.getfixturevalue(FIXTURE_POR_ROL[rol]))
        assert _pedir(client, ruta).status_code == 403, rol


@pytest.mark.parametrize("ruta", CON_MODULO, ids=_id)
def test_modulo_inhabilitado_bloquea_todas_sus_rutas(client, usuario_administrador, ruta):
    """RQF031: con el módulo inhabilitado para el rol, ninguna de sus rutas abre."""
    modulo = Modulo.objects.create(codigo_modulo=ruta["modulo"], nombre_modulo="Módulo")
    PermisoRolModulo.objects.create(rol=usuario_administrador.rol, modulo=modulo, habilitado=False)
    client.force_login(usuario_administrador)
    assert _pedir(client, ruta).status_code == 403


def test_fuerza_bruta_bloquea_el_inicio_de_sesion(client, usuario_junior, settings):
    """django-axes: tras los intentos fallidos permitidos, ni la clave correcta entra."""
    url = reverse("seguridad:iniciar_sesion")
    for _ in range(settings.AXES_FAILURE_LIMIT):
        client.post(url, {"username": usuario_junior.correo, "password": "clave-equivocada"})

    respuesta = client.post(url, {"username": usuario_junior.correo, "password": CLAVE_PRUEBAS})

    assert respuesta.status_code in (403, 429)
    assert "_auth_user_id" not in client.session


def test_las_contrasenas_no_se_guardan_en_texto_plano(usuario_junior):
    assert CLAVE_PRUEBAS not in usuario_junior.password
    assert usuario_junior.check_password(CLAVE_PRUEBAS)


def test_las_rutas_publicas_son_solo_las_previstas():
    assert {ruta["nombre"] for ruta in RUTAS if ruta["publica"]} == {
        "seguridad:iniciar_sesion",
        "finanzas:pdf_publico",
        "robots",
    }
