"""Pruebas de vistas, permisos y seguridad del módulo 7: comunicaciones integradas."""

import pytest
from django.urls import NoReverseMatch, reverse

from aplicaciones.comunicaciones.models import Comunicacion
from aplicaciones.seguridad.models import Modulo, PermisoRolModulo

pytestmark = pytest.mark.django_db


def _datos(cliente_pk, **extra):
    datos = {
        "cliente": cliente_pk,
        "canal": "Llamada",
        "fecha_hora": "2026-09-30T09:30",
        "contenido_resumen": "<script>alert(1)</script>",
    }
    datos.update(extra)
    return datos


# ---------------------------------------------------------------------------
# Acceso sin sesión / módulo inhabilitado
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nombre_url", ["comunicaciones:lista", "comunicaciones:registrar"])
def test_urls_requieren_sesion(client, nombre_url):
    respuesta = client.get(reverse(nombre_url))
    assert respuesta.status_code == 302
    assert reverse("seguridad:iniciar_sesion") in respuesta.url


def test_lista_requiere_modulo_habilitado(client, usuario_administrador):
    modulo = Modulo.objects.create(codigo_modulo=Modulo.MOD07_COMUNICACIONES, nombre_modulo="Comunicaciones")
    PermisoRolModulo.objects.create(rol=usuario_administrador.rol, modulo=modulo, habilitado=False)
    client.force_login(usuario_administrador)
    assert client.get(reverse("comunicaciones:lista")).status_code == 403


# ---------------------------------------------------------------------------
# Consulta
# ---------------------------------------------------------------------------


def test_historial_distingue_automaticas_de_manuales(
    client, usuario_senior, comunicacion_automatica, comunicacion_manual_junior
):
    client.force_login(usuario_senior)
    contenido = client.get(reverse("comunicaciones:lista")).content.decode()
    assert "be-teal" in contenido and "Automática" in contenido
    assert "be-n" in contenido and "Manual" in contenido
    assert "Origen: Honorarios" in contenido


def test_historial_del_cliente_filtra_por_canal(
    client, usuario_administrador, comunicacion_automatica, cliente
):
    Comunicacion.objects.create(cliente=cliente, canal=Comunicacion.LLAMADA, tipo=Comunicacion.MANUAL)
    client.force_login(usuario_administrador)
    url = reverse("comunicaciones:cliente", kwargs={"pk_cliente": cliente.pk})
    respuesta = client.get(url, {"canal": Comunicacion.CORREO})
    assert list(respuesta.context["comunicaciones"]) == [comunicacion_automatica]


def test_ficha_del_cliente_muestra_pestana_comunicaciones(
    client, usuario_administrador, comunicacion_automatica, cliente
):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("clientes:detalle", kwargs={"pk": cliente.pk}))
    assert "tab-comunicaciones" in respuesta.content.decode()
    assert list(respuesta.context["comunicaciones"]) == [comunicacion_automatica]
    assert respuesta.context["puede_registrar_comunicacion"] is True


def test_junior_ve_las_comunicaciones_de_todos_los_clientes_sin_registrar(
    client, usuario_junior, comunicacion_automatica, comunicacion_manual_junior
):
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("comunicaciones:lista"))
    assert set(respuesta.context["comunicaciones"]) == {comunicacion_automatica, comunicacion_manual_junior}
    assert respuesta.context["puede_registrar"] is False
    assert "Registrar comunicación" not in respuesta.content.decode()


def test_junior_abre_el_historial_de_cualquier_cliente(client, usuario_junior, cliente):
    client.force_login(usuario_junior)
    url = reverse("comunicaciones:cliente", kwargs={"pk_cliente": cliente.pk})
    assert client.get(url).status_code == 200


def test_junior_no_ve_boton_registrar_en_la_ficha(client, usuario_junior, cliente_junior):
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("clientes:detalle", kwargs={"pk": cliente_junior.pk}))
    assert respuesta.context["puede_registrar_comunicacion"] is False


# ---------------------------------------------------------------------------
# Registro manual
# ---------------------------------------------------------------------------


def test_registrar_via_ajax_devuelve_fragmento_de_modal(client, usuario_senior, cliente):
    client.force_login(usuario_senior)
    respuesta = client.get(
        reverse("comunicaciones:registrar"),
        {"cliente": cliente.pk},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert "modal-header" in respuesta.content.decode()


@pytest.mark.parametrize("nombre_usuario", ["usuario_administrador", "usuario_senior"])
def test_administrador_y_senior_registran(client, request, nombre_usuario, cliente):
    usuario = request.getfixturevalue(nombre_usuario)
    client.force_login(usuario)
    respuesta = client.post(reverse("comunicaciones:registrar"), _datos(cliente.pk))
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("comunicaciones:cliente", kwargs={"pk_cliente": cliente.pk})
    comunicacion = Comunicacion.objects.get()
    assert comunicacion.tipo == Comunicacion.MANUAL
    assert comunicacion.usuario == usuario


def test_junior_no_registra(client, usuario_junior, cliente_junior):
    client.force_login(usuario_junior)
    assert client.get(reverse("comunicaciones:registrar")).status_code == 403
    assert client.post(reverse("comunicaciones:registrar"), _datos(cliente_junior.pk)).status_code == 403
    assert not Comunicacion.objects.exists()


def test_registro_invalido_vuelve_al_formulario(client, usuario_administrador, cliente):
    client.force_login(usuario_administrador)
    respuesta = client.post(reverse("comunicaciones:registrar"), _datos(cliente.pk, canal=""))
    assert respuesta.status_code == 200
    assert not Comunicacion.objects.exists()


def test_contenido_se_escapa(client, usuario_administrador, cliente):
    client.force_login(usuario_administrador)
    client.post(reverse("comunicaciones:registrar"), _datos(cliente.pk))
    contenido = client.get(
        reverse("comunicaciones:cliente", kwargs={"pk_cliente": cliente.pk})
    ).content.decode()
    assert "<script>alert(1)</script>" not in contenido
    assert "&lt;script&gt;" in contenido


def test_no_existen_rutas_para_editar_o_eliminar():
    for nombre in ("comunicaciones:editar", "comunicaciones:eliminar"):
        with pytest.raises(NoReverseMatch):
            reverse(nombre, kwargs={"pk": 1})


# ---------------------------------------------------------------------------
# CSRF e inyección
# ---------------------------------------------------------------------------


def test_post_sin_csrf_es_rechazado(usuario_administrador, cliente):
    from django.test import Client

    cliente_http = Client(enforce_csrf_checks=True)
    cliente_http.force_login(usuario_administrador)
    assert cliente_http.post(reverse("comunicaciones:registrar"), _datos(cliente.pk)).status_code == 403


def test_filtro_con_valor_inyectado_no_rompe(client, usuario_administrador, comunicacion_automatica):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("comunicaciones:lista"), {"canal": "' OR 1=1 --", "tipo": "x"})
    assert respuesta.status_code == 200
    # Valores fuera de las opciones invalidan el filtro y se muestra todo, sin error.
    assert list(respuesta.context["comunicaciones"]) == [comunicacion_automatica]
