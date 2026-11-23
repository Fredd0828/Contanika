"""Pruebas de vistas, permisos y seguridad del módulo 8: equipo, módulos por rol y perfil."""

from io import BytesIO

import pytest
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image as PILImage

from aplicaciones.seguridad.models import PermisoRolModulo, Usuario

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
    menu = client.get(reverse("seguridad:ayuda")).context["menu_lateral"]
    etiquetas = [item["etiqueta"] for seccion in menu for item in seccion["items"]]
    assert "Equipo y roles" not in etiquetas


# ---------------------------------------------------------------------------
# Gestión de usuarios
# ---------------------------------------------------------------------------


def _enlace_del_correo(correo):
    """Ruta del enlace de acceso que trae el correo (sin el dominio)."""
    linea = next(linea for linea in correo.body.splitlines() if "/crear-contrasena/" in linea)
    return linea[linea.index("/crear-contrasena/") :].strip()


def test_administrador_crea_usuario_y_este_crea_su_contrasena(client, usuario_administrador, rol_junior):
    client.force_login(usuario_administrador)
    datos = {"nombre": "Ana Contadora", "correo": "ana@ejemplo.co", "telefono": "", "rol": rol_junior.pk}
    respuesta = client.post(reverse("seguridad:crear_usuario"), datos)
    assert respuesta.status_code == 302
    nuevo = Usuario.objects.get(correo="ana@ejemplo.co")
    assert nuevo.rol == rol_junior
    assert not nuevo.has_usable_password()
    assert len(mail.outbox) == 1
    client.logout()

    # El usuario abre el enlace, crea su contraseña y entra.
    enlace = _enlace_del_correo(mail.outbox[0])
    formulario = client.get(enlace, follow=True)
    assert formulario.context["validlink"] is True
    respuesta = client.post(
        formulario.redirect_chain[-1][0],
        {"new_password1": CLAVE_TEMPORAL, "new_password2": CLAVE_TEMPORAL},
    )
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("seguridad:contrasena_creada")
    respuesta = client.post(
        reverse("seguridad:iniciar_sesion"), {"username": "ana@ejemplo.co", "password": CLAVE_TEMPORAL}
    )
    assert respuesta.status_code == 302

    # El mismo enlace ya no sirve.
    client.logout()
    assert client.get(enlace, follow=True).context["validlink"] is False


def test_si_el_correo_falla_el_listado_muestra_el_enlace_una_vez(
    client, usuario_administrador, rol_junior, monkeypatch
):
    from aplicaciones.seguridad import servicios

    def rechazar(*args, **kwargs):
        raise OSError("SMTP caído")

    monkeypatch.setattr(servicios, "send_mail", rechazar)
    client.force_login(usuario_administrador)
    datos = {"nombre": "Luis", "correo": "luis@ejemplo.co", "telefono": "", "rol": rol_junior.pk}
    respuesta = client.post(reverse("seguridad:crear_usuario"), datos, follow=True)
    contenido = respuesta.content.decode()
    assert "No se pudo enviar el correo" in contenido
    assert "/crear-contrasena/" in contenido
    assert respuesta.context["enlace_manual"]["correo"] == "luis@ejemplo.co"
    assert "Acceso pendiente" in contenido

    otra_vez = client.get(reverse("seguridad:usuarios"))
    assert otra_vez.context["enlace_manual"] is None
    assert "/crear-contrasena/" not in otra_vez.content.decode()


def test_administrador_reenvia_el_enlace_de_acceso(client, usuario_administrador, usuario_junior):
    client.force_login(usuario_administrador)
    respuesta = client.post(reverse("seguridad:reenviar_acceso", kwargs={"pk": usuario_junior.pk}))
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("seguridad:usuarios")
    assert mail.outbox[0].to == [usuario_junior.correo]


def test_no_se_reenvia_acceso_a_un_usuario_inactivo(client, usuario_administrador, usuario_junior):
    usuario_junior.estado = Usuario.INACTIVO
    usuario_junior.save()
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("seguridad:reenviar_acceso", kwargs={"pk": usuario_junior.pk}), follow=True
    )
    assert "inactivo" in respuesta.content.decode()
    assert mail.outbox == []


def test_editar_usuario_muestra_el_boton_de_reenviar_acceso(client, usuario_administrador, usuario_junior):
    client.force_login(usuario_administrador)
    contenido = client.get(
        reverse("seguridad:editar_usuario", kwargs={"pk": usuario_junior.pk})
    ).content.decode()
    assert reverse("seguridad:reenviar_acceso", kwargs={"pk": usuario_junior.pk}) in contenido
    assert "clave_temporal" not in contenido


def test_formulario_de_creacion_muestra_modulos_del_rol(client, usuario_administrador, modulo_clientes):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("seguridad:crear_usuario"))
    assert "datos-modulos-rol" in respuesta.content.decode()
    modulos = respuesta.context["modulos_por_rol"][usuario_administrador.rol.pk]
    assert modulo_clientes.nombre_modulo in modulos


def test_crear_segundo_administrador_pide_confirmacion(client, usuario_administrador, rol_administrador):
    client.force_login(usuario_administrador)
    datos = {"nombre": "Otro", "correo": "otro@ejemplo.co", "rol": rol_administrador.pk}
    respuesta = client.post(reverse("seguridad:crear_usuario"), datos)
    assert respuesta.status_code == 200
    assert "Confirme" in respuesta.content.decode()
    assert not Usuario.objects.filter(correo="otro@ejemplo.co").exists()

    datos["confirmar_otro_administrador"] = "on"
    assert client.post(reverse("seguridad:crear_usuario"), datos).status_code == 302
    assert Usuario.objects.filter(correo="otro@ejemplo.co").exists()


def test_editar_usuario_cambia_el_rol_sin_tocar_la_clave(
    client, usuario_administrador, usuario_junior, rol_senior
):
    client.force_login(usuario_administrador)
    datos = {
        "nombre": usuario_junior.nombre,
        "correo": usuario_junior.correo,
        "telefono": "",
        "rol": rol_senior.pk,
        "identificacion": "",
        "numero_tarjeta_profesional": "",
        "clave_temporal": CLAVE_TEMPORAL,  # Campo que ya no existe: se ignora.
    }
    respuesta = client.post(reverse("seguridad:editar_usuario", kwargs={"pk": usuario_junior.pk}), datos)
    assert respuesta.status_code == 302
    usuario_junior.refresh_from_db()
    assert usuario_junior.rol == rol_senior
    assert usuario_junior.check_password(CLAVE_PRUEBAS)
    assert mail.outbox == []


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
    menu = client.get(reverse("seguridad:ayuda")).context["menu_lateral"]
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
    assert usuario_junior.correo == "junior@ejemplo.co"  # el correo no se cambia desde el perfil


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
