"""Pruebas de «¿Olvidó su contraseña?» y de la página para crearla con el enlace del correo."""

from datetime import timedelta

import pytest
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.core.cache import cache
from django.urls import reverse

from aplicaciones.seguridad import formularios
from aplicaciones.seguridad.models import Usuario

from ..conftest import CLAVE_PRUEBAS

pytestmark = pytest.mark.django_db

CLAVE_NUEVA = "Nueva-Clave-Contanika-26"
URL_RECUPERAR = "seguridad:recuperar_contrasena"


@pytest.fixture(autouse=True)
def limpiar_limite_de_peticiones():
    """El límite por minuto se guarda en la caché: cada prueba empieza de cero."""
    cache.clear()
    yield
    cache.clear()


def _pedir_enlace(client, correo):
    return client.post(reverse(URL_RECUPERAR), {"email": correo})


def _enlace_del_correo(correo):
    linea = next(linea for linea in correo.body.splitlines() if "/crear-contrasena/" in linea)
    return linea[linea.index("/crear-contrasena/") :].strip()


def _crear_clave(client, enlace, clave=CLAVE_NUEVA, repetida=None):
    """Abre el enlace (Django lo cambia por una dirección sin el token) y envía la clave nueva."""
    formulario = client.get(enlace, follow=True)
    if not formulario.context["validlink"]:
        return formulario
    return client.post(
        formulario.redirect_chain[-1][0],
        {"new_password1": clave, "new_password2": repetida or clave},
    )


# ---------------------------------------------------------------------------
# Pedir el enlace
# ---------------------------------------------------------------------------


def test_la_pagina_es_publica_y_el_inicio_de_sesion_la_enlaza(client):
    assert client.get(reverse(URL_RECUPERAR)).status_code == 200
    assert reverse(URL_RECUPERAR) in client.get(reverse("seguridad:iniciar_sesion")).content.decode()


def test_un_usuario_activo_recibe_el_enlace_y_crea_su_nueva_clave(client, usuario_junior, settings):
    settings.URL_SITIO = "https://contanika.ejemplo.co"
    respuesta = _pedir_enlace(client, usuario_junior.correo.upper())
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("seguridad:recuperar_enviado")
    assert len(mail.outbox) == 1
    correo = mail.outbox[0]
    assert correo.to == [usuario_junior.correo]
    assert correo.subject == "Contanika: enlace para crear una nueva contraseña"
    assert "https://contanika.ejemplo.co/crear-contrasena/" in correo.body

    # Hasta que cree la nueva, la contraseña actual sigue sirviendo.
    usuario_junior.refresh_from_db()
    assert usuario_junior.check_password(CLAVE_PRUEBAS)

    respuesta = _crear_clave(client, _enlace_del_correo(correo))
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("seguridad:contrasena_creada")
    usuario_junior.refresh_from_db()
    assert usuario_junior.check_password(CLAVE_NUEVA)
    assert "_auth_user_id" not in client.session  # No entra solo: debe iniciar sesión.


@pytest.mark.parametrize("caso", ["no_existe", "inactivo"])
def test_la_respuesta_no_revela_si_la_cuenta_existe(client, usuario_junior, caso):
    correo = "nadie@ejemplo.co"
    if caso == "inactivo":
        usuario_junior.estado = Usuario.INACTIVO
        usuario_junior.save()
        correo = usuario_junior.correo
    respuesta = _pedir_enlace(client, correo)
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("seguridad:recuperar_enviado")
    assert mail.outbox == []


def test_quien_aun_no_crea_su_clave_tambien_puede_pedir_el_enlace(client, usuario_junior):
    usuario_junior.set_unusable_password()
    usuario_junior.save()
    _pedir_enlace(client, usuario_junior.correo)
    assert len(mail.outbox) == 1


def test_si_el_servidor_de_correo_falla_la_respuesta_es_la_misma(client, usuario_junior, monkeypatch):
    def rechazar(*args, **kwargs):
        raise OSError("SMTP caído")

    monkeypatch.setattr(formularios.PasswordResetForm, "send_mail", rechazar)
    respuesta = _pedir_enlace(client, usuario_junior.correo)
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("seguridad:recuperar_enviado")


def test_la_pagina_de_enviado_carga(client):
    respuesta = client.get(reverse("seguridad:recuperar_enviado"))
    assert respuesta.status_code == 200
    assert "3 días" in respuesta.content.decode()


def test_se_limitan_los_pedidos_por_minuto(client, usuario_junior):
    for _ in range(5):
        _pedir_enlace(client, usuario_junior.correo)
    respuesta = _pedir_enlace(client, usuario_junior.correo)
    assert respuesta.status_code == 429
    assert len(mail.outbox) == 5


# ---------------------------------------------------------------------------
# Crear la contraseña con el enlace
# ---------------------------------------------------------------------------


@pytest.fixture
def enlace_junior(client, usuario_junior):
    _pedir_enlace(client, usuario_junior.correo)
    return _enlace_del_correo(mail.outbox[0])


def test_el_enlace_sirve_una_sola_vez(client, usuario_junior, enlace_junior):
    _crear_clave(client, enlace_junior)
    segunda = _crear_clave(client, enlace_junior, clave="Otra-Clave-Distinta-99")
    assert segunda.context["validlink"] is False
    assert "ya no sirve" in segunda.content.decode()
    usuario_junior.refresh_from_db()
    assert usuario_junior.check_password(CLAVE_NUEVA)


def test_el_enlace_vence(client, usuario_junior, enlace_junior, monkeypatch, settings):
    original = PasswordResetTokenGenerator._now
    vencido = lambda self: original(self) + timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT + 60)  # noqa: E731
    monkeypatch.setattr(PasswordResetTokenGenerator, "_now", vencido)
    respuesta = _crear_clave(client, enlace_junior)
    assert respuesta.context["validlink"] is False
    usuario_junior.refresh_from_db()
    assert usuario_junior.check_password(CLAVE_PRUEBAS)


def test_el_enlace_no_sirve_si_el_usuario_quedo_inactivo(client, usuario_junior, enlace_junior):
    usuario_junior.estado = Usuario.INACTIVO
    usuario_junior.save()
    respuesta = _crear_clave(client, enlace_junior)
    assert respuesta.context["validlink"] is False


def test_un_enlace_inventado_no_sirve(client):
    respuesta = client.get(reverse("seguridad:crear_contrasena", kwargs={"uidb64": "MQ", "token": "abc-123"}))
    assert respuesta.status_code == 200
    assert respuesta.context["validlink"] is False


@pytest.mark.parametrize(
    "clave, repetida",
    [("12345", None), ("1234567890", None), (CLAVE_NUEVA, "Otra-Distinta-2026")],
    ids=["corta", "solo-numeros", "no-coinciden"],
)
def test_la_clave_debe_cumplir_las_reglas(client, usuario_junior, enlace_junior, clave, repetida):
    respuesta = _crear_clave(client, enlace_junior, clave=clave, repetida=repetida)
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors
    usuario_junior.refresh_from_db()
    assert usuario_junior.check_password(CLAVE_PRUEBAS)


def test_la_pagina_final_lleva_al_inicio_de_sesion(client):
    respuesta = client.get(reverse("seguridad:contrasena_creada"))
    assert respuesta.status_code == 200
    assert reverse("seguridad:iniciar_sesion") in respuesta.content.decode()
