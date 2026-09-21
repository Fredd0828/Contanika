"""Pruebas de seguridad de las vistas de autenticación y acceso."""

import pytest
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse
from django.views import View

from aplicaciones.seguridad.models import Modulo, PermisoRolModulo
from aplicaciones.seguridad.permisos import ModuloHabilitadoMixin

pytestmark = pytest.mark.django_db


class VistaDeTareas(ModuloHabilitadoMixin, View):
    """Vista de prueba protegida por el módulo de tareas."""

    codigo_modulo = Modulo.MOD03_TAREAS

    def get(self, request):
        return HttpResponse("contenido protegido")


def test_panel_exige_inicio_de_sesion(client):
    """Un usuario anónimo no accede al panel; es redirigido al login."""
    respuesta = client.get(reverse("seguridad:panel"))
    assert respuesta.status_code == 302
    assert reverse("seguridad:iniciar_sesion") in respuesta.url


def test_panel_accesible_con_sesion(client, usuario_administrador):
    """Un usuario autenticado accede al panel principal."""
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("seguridad:panel"))
    assert respuesta.status_code == 200


def test_formulario_de_login_responde(client):
    """La página de inicio de sesión carga correctamente."""
    respuesta = client.get(reverse("seguridad:iniciar_sesion"))
    assert respuesta.status_code == 200
    assert "csrfmiddlewaretoken" in respuesta.content.decode()


def test_login_con_credenciales_validas(client, usuario_administrador):
    """El inicio de sesión con credenciales correctas redirige al panel."""
    respuesta = client.post(
        reverse("seguridad:iniciar_sesion"),
        {"username": "paula@befrec.co", "password": "ClaveSegura123"},
    )
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("seguridad:panel")


def test_modulo_inhabilitado_bloquea_la_vista(usuario_junior, modulo_tareas):
    """El módulo inhabilitado bloquea el acceso directo por URL (RQF031)."""
    PermisoRolModulo.objects.create(rol=usuario_junior.rol, modulo=modulo_tareas, habilitado=False)
    peticion = RequestFactory().get("/tareas/")
    peticion.user = usuario_junior
    with pytest.raises(PermissionDenied):
        VistaDeTareas.as_view()(peticion)


def test_modulo_habilitado_permite_la_vista(usuario_junior, modulo_tareas):
    """Con el módulo habilitado la vista responde normalmente."""
    PermisoRolModulo.objects.create(rol=usuario_junior.rol, modulo=modulo_tareas, habilitado=True)
    peticion = RequestFactory().get("/tareas/")
    peticion.user = usuario_junior
    respuesta = VistaDeTareas.as_view()(peticion)
    assert respuesta.status_code == 200
