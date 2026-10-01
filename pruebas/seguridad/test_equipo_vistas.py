"""Pruebas de vistas, permisos y seguridad del módulo 8: equipo, módulos por rol y perfil."""

from io import BytesIO

import pytest
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image as PILImage

from aplicaciones.seguridad.models import Modulo, PermisoRolModulo, Usuario

from ..conftest import CLAVE_PRUEBAS

pytestmark = pytest.mark.django_db

CLAVE_TEMPORAL = "Temporal-Contanika-2026"
URLS_ADMIN = ["seguridad:usuarios", "seguridad:crear_usuario", "seguridad:permisos"]


def _imagen_png(nombre="yo.png"):
    buffer = BytesIO()
    PILImage.new("RGB", (10, 10), color="teal").save(buffer, format="PNG")
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type="image/png")


@pytest.fixture(autouse=True)
def media_root_temporal(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


# ---------------------------------------------------------------------------
# Acceso
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nombre_url", URLS_ADMIN + ["seguridad:equipo", "seguridad:perfil"])
def test_urls_requieren_sesion(client, nombre_url):
    respuesta = client.get(reverse(nombre_url))
    assert respuesta.status_code == 302
    assert reverse("seguridad:iniciar_sesion") in respuesta.url


@pytest.mark.parametrize("nombre_url", URLS_ADMIN)
@pytest.mark.parametrize("nombre_usuario", ["usuario_senior", "usuario_junior"])
def test_solo_el_administrador_gestiona_el_equipo(client, request, nombre_url, nombre_usuario):
    client.force_login(request.getfixturevalue(nombre_usuario))
    respuesta = client.get(reverse(nombre_url))
    assert respuesta.status_code == 403
    assert "Acceso no disponible" in respuesta.content.decode()


def test_senior_consulta_el_panel_de_equipo(client, usuario_senior):
    client.force_login(usuario_senior)
    respuesta = client.get(reverse("seguridad:equipo"))
    assert respuesta.status_code == 200
    assert "Usuarios" not in respuesta.content.decode().split("Trabajo del equipo")[0]


def test_junior_no_ve_panel_de_equipo_ni_el_menu(client, usuario_junior):
    client.force_login(usuario_junior)
    assert client.get(reverse("seguridad:equipo")).status_code == 403
    menu = client.get(reverse("seguridad:panel")).context["menu_lateral"]
    etiquetas = [item["etiqueta"] for seccion in menu for item in seccion["items"]]
    assert "Equipo y roles" not in etiquetas


def test_panel_principal_enlaza_modulos_construidos(client, usuario_administrador):
    for codigo, nombre in (
        (Modulo.MOD07_COMUNICACIONES, "Comunicaciones"),
        (Modulo.MOD09_EXPEDIENTE, "Expediente"),
    ):
        Modulo.objects.create(codigo_modulo=codigo, nombre_modulo=nombre)
    client.force_login(usuario_administrador)
    modulos = {
        m["modulo"].codigo_modulo: m["url"] for m in client.get(reverse("seguridad:panel")).context["modulos"]
    }
    assert modulos == {
        Modulo.MOD07_COMUNICACIONES: "comunicaciones:lista",
        Modulo.MOD09_EXPEDIENTE: "expediente:lista",
    }


# ---------------------------------------------------------------------------
# Gestión de usuarios
# ---------------------------------------------------------------------------


def test_administrador_crea_usuario(client, usuario_administrador, rol_junior):
    client.force_login(usuario_administrador)
    datos = {
        "nombre": "Ana Contadora",
        "correo": "ana@befrec.co",
        "telefono": "",
        "rol": rol_junior.pk,
        "clave_temporal": CLAVE_TEMPORAL,
    }
    respuesta = client.post(reverse("seguridad:crear_usuario"), datos)
    assert respuesta.status_code == 302
    nuevo = Usuario.objects.get(correo="ana@befrec.co")
    assert nuevo.rol == rol_junior
    assert len(mail.outbox) == 1
    client.logout()
    respuesta = client.post(
        reverse("seguridad:iniciar_sesion"), {"username": "ana@befrec.co", "password": CLAVE_TEMPORAL}
    )
    assert respuesta.status_code == 302


def test_formulario_de_creacion_muestra_modulos_del_rol(client, usuario_administrador, modulo_clientes):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("seguridad:crear_usuario"))
    assert "datos-modulos-rol" in respuesta.content.decode()
    modulos = respuesta.context["modulos_por_rol"][usuario_administrador.rol.pk]
    assert modulo_clientes.nombre_modulo in modulos


def test_crear_segundo_administrador_pide_confirmacion(client, usuario_administrador, rol_administrador):
    client.force_login(usuario_administrador)
    datos = {
        "nombre": "Otro",
        "correo": "otro@befrec.co",
        "rol": rol_administrador.pk,
        "clave_temporal": CLAVE_TEMPORAL,
    }
    respuesta = client.post(reverse("seguridad:crear_usuario"), datos)
    assert respuesta.status_code == 200
    assert "Confirme" in respuesta.content.decode()
    assert not Usuario.objects.filter(correo="otro@befrec.co").exists()

    datos["confirmar_otro_administrador"] = "on"
    assert client.post(reverse("seguridad:crear_usuario"), datos).status_code == 302
    assert Usuario.objects.filter(correo="otro@befrec.co").exists()


def test_editar_usuario_cambia_rol_y_clave(client, usuario_administrador, usuario_junior, rol_senior):
    client.force_login(usuario_administrador)
    datos = {
        "nombre": usuario_junior.nombre,
        "correo": usuario_junior.correo,
        "telefono": "",
        "rol": rol_senior.pk,
        "identificacion": "",
        "numero_tarjeta_profesional": "",
        "clave_temporal": CLAVE_TEMPORAL,
    }
    respuesta = client.post(reverse("seguridad:editar_usuario", kwargs={"pk": usuario_junior.pk}), datos)
    assert respuesta.status_code == 302
    usuario_junior.refresh_from_db()
    assert usuario_junior.rol == rol_senior
    assert usuario_junior.check_password(CLAVE_TEMPORAL)
    assert "nueva contraseña temporal" in mail.outbox[0].subject


def test_no_puede_quitarse_el_rol_si_es_el_unico_administrador(client, usuario_administrador, rol_senior):
    client.force_login(usuario_administrador)
    datos = {
        "nombre": usuario_administrador.nombre,
        "correo": usuario_administrador.correo,
        "rol": rol_senior.pk,
    }
    respuesta = client.post(
        reverse("seguridad:editar_usuario", kwargs={"pk": usuario_administrador.pk}), datos
    )
    assert respuesta.status_code == 200
    assert "al menos un Administrador" in respuesta.content.decode()
    usuario_administrador.refresh_from_db()
    assert usuario_administrador.es_administrador


def test_inactivar_y_activar_usuario(client, usuario_administrador, usuario_junior):
    client.force_login(usuario_administrador)
    url = reverse("seguridad:estado_usuario", kwargs={"pk": usuario_junior.pk})
    client.post(url)
    usuario_junior.refresh_from_db()
    assert usuario_junior.estado == Usuario.INACTIVO
    client.post(url)
    usuario_junior.refresh_from_db()
    assert usuario_junior.estado == Usuario.ACTIVO


def test_eliminar_usuario_con_historial_muestra_aviso(
    client, usuario_administrador, usuario_junior, cliente_junior
):
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("seguridad:eliminar_usuario", kwargs={"pk": usuario_junior.pk}), follow=True
    )
    assert "Inactívelo" in respuesta.content.decode()
    assert Usuario.objects.filter(pk=usuario_junior.pk).exists()


def test_listado_filtra_por_rol(client, usuario_administrador, usuario_junior, rol_junior):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("seguridad:usuarios"), {"rol": rol_junior.pk})
    assert list(respuesta.context["usuarios"]) == [usuario_junior]


def test_post_sin_csrf_es_rechazado(usuario_administrador, usuario_junior):
    from django.test import Client

    cliente_http = Client(enforce_csrf_checks=True)
    cliente_http.force_login(usuario_administrador)
    url = reverse("seguridad:estado_usuario", kwargs={"pk": usuario_junior.pk})
    assert cliente_http.post(url).status_code == 403


# ---------------------------------------------------------------------------
# Módulos por rol
# ---------------------------------------------------------------------------


def test_inhabilitar_modulo_lo_quita_del_menu_y_bloquea_la_url(
    client, usuario_administrador, usuario_junior, modulo_clientes
):
    client.force_login(usuario_administrador)
    # Se envía la matriz sin marcar Clientes para el Junior.
    datos = {f"permiso_{usuario_administrador.rol.pk}_{modulo_clientes.pk}": "on"}
    client.post(reverse("seguridad:permisos"), datos)
    assert not PermisoRolModulo.objects.get(rol=usuario_junior.rol, modulo=modulo_clientes).habilitado

    client.force_login(usuario_junior)
    menu = client.get(reverse("seguridad:panel")).context["menu_lateral"]
    etiquetas = [item["etiqueta"] for seccion in menu for item in seccion["items"]]
    assert "Clientes" not in etiquetas
    respuesta = client.get(reverse("clientes:lista"))
    assert respuesta.status_code == 403
    assert "no está habilitado" in respuesta.content.decode()


def test_perfil_sigue_disponible_con_todo_inhabilitado(client, usuario_junior, modulo_clientes):
    PermisoRolModulo.objects.create(rol=usuario_junior.rol, modulo=modulo_clientes, habilitado=False)
    client.force_login(usuario_junior)
    assert client.get(reverse("seguridad:perfil")).status_code == 200


def test_claves_invalidas_en_permisos_se_ignoran(client, usuario_administrador):
    client.force_login(usuario_administrador)
    respuesta = client.post(reverse("seguridad:permisos"), {"permiso_x_y": "on", "permiso_1": "on"})
    assert respuesta.status_code == 302


# ---------------------------------------------------------------------------
# Perfil propio (HU024)
# ---------------------------------------------------------------------------


def test_perfil_actualiza_nombre_telefono_y_foto(client, usuario_junior):
    client.force_login(usuario_junior)
    foto = _imagen_png()
    datos = {"nombre": "Junior Actualizado", "telefono": "3005556677", "foto": foto, "correo": "hack@x.co"}
    respuesta = client.post(reverse("seguridad:perfil"), datos)
    assert respuesta.status_code == 302
    usuario_junior.refresh_from_db()
    assert usuario_junior.nombre == "Junior Actualizado"
    assert usuario_junior.foto.name.startswith("fotos/")
    assert usuario_junior.correo == "junior@befrec.co"  # el correo no se cambia desde el perfil


def test_perfil_del_junior_no_muestra_firma(client, usuario_junior):
    client.force_login(usuario_junior)
    assert "firma" not in client.get(reverse("seguridad:perfil")).context["formulario"].fields


def test_perfil_del_senior_incluye_firma_y_tarjeta(client, usuario_senior):
    client.force_login(usuario_senior)
    campos = client.get(reverse("seguridad:perfil")).context["formulario"].fields
    assert {"firma", "numero_tarjeta_profesional", "identificacion"} <= set(campos)


def test_cambiar_clave_exige_la_actual(client, usuario_junior):
    client.force_login(usuario_junior)
    datos = {"old_password": "equivocada", "new_password1": CLAVE_TEMPORAL, "new_password2": CLAVE_TEMPORAL}
    respuesta = client.post(reverse("seguridad:cambiar_clave"), datos)
    assert respuesta.status_code == 200
    usuario_junior.refresh_from_db()
    assert usuario_junior.check_password(CLAVE_PRUEBAS)


def test_cambiar_clave_conserva_la_sesion(client, usuario_junior):
    client.force_login(usuario_junior)
    datos = {"old_password": CLAVE_PRUEBAS, "new_password1": CLAVE_TEMPORAL, "new_password2": CLAVE_TEMPORAL}
    respuesta = client.post(reverse("seguridad:cambiar_clave"), datos)
    assert respuesta.status_code == 302
    usuario_junior.refresh_from_db()
    assert usuario_junior.check_password(CLAVE_TEMPORAL)
    assert client.get(reverse("seguridad:perfil")).status_code == 200
