"""Pruebas de vistas, permisos y seguridad del módulo 9: expediente y bitácora."""

import pytest
from django.urls import reverse

from aplicaciones.comunes.models import Adjunto
from aplicaciones.expediente.models import Anotacion
from aplicaciones.seguridad.models import Modulo, PermisoRolModulo

from .conftest import archivo_prueba

pytestmark = pytest.mark.django_db

URLS_PROTEGIDAS = ["expediente:lista", "expediente:crear"]


def _datos(cliente_pk, **extra):
    datos = {
        "cliente": cliente_pk,
        "tipo_anotacion": "Reunión",
        "fecha": "2026-09-30",
        "contenido": "<script>alert(1)</script>",
    }
    datos.update(extra)
    return datos


def _adjuntar(anotacion, nombre="soporte.pdf"):
    return Adjunto.objects.create(
        tabla_origen=Adjunto.ANOTACION,
        id_origen=anotacion.pk,
        archivo=archivo_prueba(nombre),
        nombre_archivo=nombre,
    )


# ---------------------------------------------------------------------------
# Acceso sin sesión / módulo inhabilitado
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nombre_url", URLS_PROTEGIDAS)
def test_urls_requieren_sesion(client, nombre_url):
    respuesta = client.get(reverse(nombre_url))
    assert respuesta.status_code == 302
    assert reverse("seguridad:iniciar_sesion") in respuesta.url


def test_lista_requiere_modulo_habilitado(client, usuario_administrador):
    modulo = Modulo.objects.create(codigo_modulo=Modulo.MOD09_EXPEDIENTE, nombre_modulo="Expediente")
    PermisoRolModulo.objects.create(rol=usuario_administrador.rol, modulo=modulo, habilitado=False)
    client.force_login(usuario_administrador)
    assert client.get(reverse("expediente:lista")).status_code == 403


# ---------------------------------------------------------------------------
# Consulta
# ---------------------------------------------------------------------------


def test_lista_general_muestra_anotaciones_y_adjuntos(client, usuario_senior, anotacion_cliente):
    _adjuntar(anotacion_cliente, "retencion_febrero.pdf")
    client.force_login(usuario_senior)
    respuesta = client.get(reverse("expediente:lista"))
    assert respuesta.status_code == 200
    assert "Se presentó la retención" in respuesta.content.decode()
    assert "retencion_febrero.pdf" in respuesta.content.decode()


def test_expediente_del_cliente_filtra_por_tipo_y_fecha(
    client, usuario_administrador, anotacion_cliente, cliente
):
    Anotacion.objects.create(
        cliente=cliente, usuario=usuario_administrador, tipo_anotacion="Llamada", contenido="Otra"
    )
    client.force_login(usuario_administrador)
    url = reverse("expediente:cliente", kwargs={"pk_cliente": cliente.pk})
    respuesta = client.get(
        url, {"tipo": "Retención en la fuente", "desde": "2026-03-01", "hasta": "2026-03-31"}
    )
    assert list(respuesta.context["anotaciones"]) == [anotacion_cliente]


def test_archivadas_solo_con_el_filtro(client, usuario_senior, anotacion_cliente, cliente):
    anotacion_cliente.archivar()
    client.force_login(usuario_senior)
    url = reverse("expediente:cliente", kwargs={"pk_cliente": cliente.pk})
    assert list(client.get(url).context["anotaciones"]) == []
    respuesta = client.get(url, {"incluir_archivadas": "on"})
    assert list(respuesta.context["anotaciones"]) == [anotacion_cliente]
    assert "Archivada" in respuesta.content.decode()


def test_ficha_del_cliente_muestra_pestana_expediente(
    client, usuario_administrador, anotacion_cliente, cliente
):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("clientes:detalle", kwargs={"pk": cliente.pk}))
    assert "tab-expediente" in respuesta.content.decode()
    assert list(respuesta.context["anotaciones"]) == [anotacion_cliente]


def test_junior_abre_el_expediente_de_cualquier_cliente_sin_poder_anotar_en_los_ajenos(
    client, usuario_junior, cliente
):
    client.force_login(usuario_junior)
    url = reverse("expediente:cliente", kwargs={"pk_cliente": cliente.pk})
    respuesta = client.get(url)
    assert respuesta.status_code == 200
    assert respuesta.context["puede_anotar"] is False
    assert "Nueva anotación" not in respuesta.content.decode()


def test_junior_puede_anotar_en_el_expediente_de_su_cliente(client, usuario_junior, cliente_junior):
    client.force_login(usuario_junior)
    url = reverse("expediente:cliente", kwargs={"pk_cliente": cliente_junior.pk})
    assert client.get(url).context["puede_anotar"] is True


def test_junior_en_lista_general_ve_las_anotaciones_de_todos_los_clientes(
    client, usuario_junior, anotacion_cliente, anotacion_cliente_junior
):
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("expediente:lista"))
    assert set(respuesta.context["anotaciones"]) == {anotacion_cliente, anotacion_cliente_junior}


# ---------------------------------------------------------------------------
# Registro de anotaciones
# ---------------------------------------------------------------------------


def test_crear_via_ajax_devuelve_fragmento_de_modal(client, usuario_administrador, cliente):
    client.force_login(usuario_administrador)
    respuesta = client.get(
        reverse("expediente:crear"), {"cliente": cliente.pk}, headers={"X-Requested-With": "XMLHttpRequest"}
    )
    contenido = respuesta.content.decode()
    assert "modal-header" in contenido
    assert 'enctype="multipart/form-data"' in contenido


def test_senior_crea_anotacion_con_adjuntos(client, usuario_senior, cliente):
    client.force_login(usuario_senior)
    datos = _datos(cliente.pk, archivos=[archivo_prueba("acta.pdf"), archivo_prueba("lista.pdf")])
    respuesta = client.post(reverse("expediente:crear"), datos)
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("expediente:cliente", kwargs={"pk_cliente": cliente.pk})
    anotacion = Anotacion.objects.get()
    assert anotacion.usuario == usuario_senior
    assert Adjunto.objects.filter(tabla_origen=Adjunto.ANOTACION, id_origen=anotacion.pk).count() == 2


def test_contenido_se_escapa(client, usuario_administrador, cliente):
    client.force_login(usuario_administrador)
    client.post(reverse("expediente:crear"), _datos(cliente.pk))
    respuesta = client.get(reverse("expediente:cliente", kwargs={"pk_cliente": cliente.pk}))
    contenido = respuesta.content.decode()
    assert "<script>alert(1)</script>" not in contenido
    assert "&lt;script&gt;" in contenido


def test_junior_crea_en_su_cliente(client, usuario_junior, cliente_junior):
    client.force_login(usuario_junior)
    respuesta = client.post(reverse("expediente:crear"), _datos(cliente_junior.pk))
    assert respuesta.status_code == 302
    assert Anotacion.objects.get().usuario == usuario_junior


def test_junior_no_crea_en_cliente_ajeno(client, usuario_junior, cliente):
    client.force_login(usuario_junior)
    respuesta = client.post(reverse("expediente:crear"), _datos(cliente.pk))
    assert respuesta.status_code == 200
    assert not Anotacion.objects.exists()


def test_junior_maximo_tres_adjuntos(client, usuario_junior, cliente_junior):
    client.force_login(usuario_junior)
    archivos = [archivo_prueba(f"{i}.pdf") for i in range(4)]
    respuesta = client.post(reverse("expediente:crear"), _datos(cliente_junior.pk, archivos=archivos))
    assert respuesta.status_code == 200
    assert not Anotacion.objects.exists()
    assert not Adjunto.objects.exists()


def test_no_existen_rutas_para_editar_o_eliminar():
    from django.urls import NoReverseMatch

    for nombre in ("expediente:editar", "expediente:eliminar"):
        with pytest.raises(NoReverseMatch):
            reverse(nombre, kwargs={"pk": 1})


# ---------------------------------------------------------------------------
# Archivar y restaurar
# ---------------------------------------------------------------------------


def test_administrador_archiva_y_restaura(client, usuario_administrador, anotacion_cliente):
    client.force_login(usuario_administrador)
    client.post(reverse("expediente:archivar", kwargs={"pk": anotacion_cliente.pk}))
    anotacion_cliente.refresh_from_db()
    assert anotacion_cliente.archivado is True
    client.post(reverse("expediente:restaurar", kwargs={"pk": anotacion_cliente.pk}))
    anotacion_cliente.refresh_from_db()
    assert anotacion_cliente.archivado is False


@pytest.mark.parametrize("nombre_usuario", ["usuario_senior", "usuario_junior"])
def test_otros_roles_no_archivan(client, request, nombre_usuario, anotacion_cliente_junior):
    usuario = request.getfixturevalue(nombre_usuario)
    client.force_login(usuario)
    respuesta = client.post(reverse("expediente:archivar", kwargs={"pk": anotacion_cliente_junior.pk}))
    assert respuesta.status_code == 403
    anotacion_cliente_junior.refresh_from_db()
    assert anotacion_cliente_junior.archivado is False


def test_archivar_por_get_no_esta_permitido(client, usuario_administrador, anotacion_cliente):
    client.force_login(usuario_administrador)
    assert client.get(reverse("expediente:archivar", kwargs={"pk": anotacion_cliente.pk})).status_code == 405


# ---------------------------------------------------------------------------
# Descarga de adjuntos
# ---------------------------------------------------------------------------


def test_descargar_adjunto(client, usuario_senior, anotacion_cliente):
    adjunto = _adjuntar(anotacion_cliente, "retencion.pdf")
    client.force_login(usuario_senior)
    respuesta = client.get(reverse("expediente:descargar_adjunto", kwargs={"pk": adjunto.pk}))
    assert respuesta.status_code == 200
    assert "retencion.pdf" in respuesta["Content-Disposition"]
    assert b"".join(respuesta.streaming_content).startswith(b"%PDF")


def test_junior_descarga_adjunto_de_cualquier_cliente(client, usuario_junior, anotacion_cliente):
    adjunto = _adjuntar(anotacion_cliente)
    client.force_login(usuario_junior)
    assert client.get(reverse("expediente:descargar_adjunto", kwargs={"pk": adjunto.pk})).status_code == 200


def test_no_descarga_adjunto_de_hallazgo_por_esta_ruta(client, usuario_administrador, anotacion_cliente):
    adjunto = Adjunto.objects.create(
        tabla_origen=Adjunto.HALLAZGO,
        id_origen=anotacion_cliente.pk,
        archivo=archivo_prueba(),
        nombre_archivo="hallazgo.pdf",
    )
    client.force_login(usuario_administrador)
    assert client.get(reverse("expediente:descargar_adjunto", kwargs={"pk": adjunto.pk})).status_code == 404


# ---------------------------------------------------------------------------
# CSRF e inyección
# ---------------------------------------------------------------------------


def test_post_sin_csrf_es_rechazado(usuario_administrador, cliente):
    from django.test import Client

    cliente_http = Client(enforce_csrf_checks=True)
    cliente_http.force_login(usuario_administrador)
    respuesta = cliente_http.post(reverse("expediente:crear"), _datos(cliente.pk))
    assert respuesta.status_code == 403


def test_filtro_resiste_inyeccion_sql(client, usuario_administrador, anotacion_cliente):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("expediente:lista"), {"tipo": "' OR 1=1 --"})
    assert respuesta.status_code == 200
    assert list(respuesta.context["anotaciones"]) == []
