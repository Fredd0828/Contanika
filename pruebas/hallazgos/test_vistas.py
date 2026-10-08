"""Pruebas de vistas, permisos y seguridad del módulo 5: hallazgos y revisiones contables."""

from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from aplicaciones.comunes.models import Adjunto
from aplicaciones.hallazgos.models import Hallazgo
from aplicaciones.seguridad.models import PermisoRolModulo

pytestmark = pytest.mark.django_db

URLS_PROTEGIDAS = ["hallazgos:lista", "hallazgos:crear"]


@pytest.fixture(autouse=True)
def media_root_temporal(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def hallazgo_cliente(cliente, usuario_administrador):
    return Hallazgo.objects.create(
        cliente=cliente,
        tipo_hallazgo="Inconsistencia",
        fecha_inicio_periodo=date(2026, 1, 1),
        fecha_fin_periodo=date(2026, 1, 31),
        responsable=usuario_administrador,
        descripcion="Diferencia detectada en la conciliación bancaria.",
    )


@pytest.fixture
def hallazgo_cliente_junior(cliente_junior, usuario_administrador):
    return Hallazgo.objects.create(
        cliente=cliente_junior,
        tipo_hallazgo="Observación",
        fecha_inicio_periodo=date(2026, 2, 1),
        fecha_fin_periodo=date(2026, 2, 28),
        responsable=usuario_administrador,
        descripcion="Falta soporte de un anticipo.",
    )


def _datos_hallazgo(cliente_pk):
    return {
        "cliente": cliente_pk,
        "tipo_hallazgo": "Inconsistencia",
        "fecha_inicio_periodo": "2026-01-01",
        "fecha_fin_periodo": "2026-01-31",
        "prioridad": Hallazgo.MEDIA,
        "descripcion": "<script>alert(1)</script>",
    }


# ---------------------------------------------------------------------------
# Acceso sin sesión / módulo inhabilitado
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nombre_url", URLS_PROTEGIDAS)
def test_urls_requieren_sesion(client, nombre_url):
    respuesta = client.get(reverse(nombre_url))
    assert respuesta.status_code == 302
    assert reverse("seguridad:iniciar_sesion") in respuesta.url


def test_lista_requiere_modulo_habilitado(client, usuario_administrador, modulo_hallazgos):
    PermisoRolModulo.objects.create(rol=usuario_administrador.rol, modulo=modulo_hallazgos, habilitado=False)
    client.force_login(usuario_administrador)
    assert client.get(reverse("hallazgos:lista")).status_code == 403


# ---------------------------------------------------------------------------
# Crear, editar
# ---------------------------------------------------------------------------


def test_crear_hallazgo(client, usuario_administrador, cliente):
    client.force_login(usuario_administrador)
    respuesta = client.post(reverse("hallazgos:crear"), _datos_hallazgo(cliente.pk))
    assert respuesta.status_code == 302
    hallazgo = Hallazgo.objects.get(cliente=cliente)
    assert hallazgo.tipo_hallazgo == "Inconsistencia"


def test_editar_hallazgo_get_muestra_formulario_precargado(client, usuario_administrador, hallazgo_cliente):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("hallazgos:editar", args=[hallazgo_cliente.pk]))
    assert respuesta.status_code == 200
    assert respuesta.context["formulario"].instance == hallazgo_cliente


def test_crear_hallazgo_via_ajax_devuelve_fragmento_de_modal(client, usuario_administrador):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("hallazgos:crear"), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert respuesta.status_code == 200
    assert b"modal-header" in respuesta.content
    assert b"<!DOCTYPE" not in respuesta.content


def test_detalle_hallazgo_via_ajax_devuelve_fragmento_de_modal(
    client, usuario_administrador, hallazgo_cliente
):
    client.force_login(usuario_administrador)
    respuesta = client.get(
        reverse("hallazgos:detalle", args=[hallazgo_cliente.pk]), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )
    assert respuesta.status_code == 200
    assert b"modal-header" in respuesta.content
    assert b"<!DOCTYPE" not in respuesta.content


def test_editar_hallazgo_escapa_descripcion_en_el_detalle(client, usuario_administrador, hallazgo_cliente):
    client.force_login(usuario_administrador)
    datos = _datos_hallazgo(hallazgo_cliente.cliente_id)
    respuesta = client.post(reverse("hallazgos:editar", args=[hallazgo_cliente.pk]), datos)
    assert respuesta.status_code == 302

    detalle = client.get(reverse("hallazgos:detalle", args=[hallazgo_cliente.pk]))
    contenido = detalle.content.decode()
    assert "<script>alert(1)</script>" not in contenido
    assert "&lt;script&gt;" in contenido


# ---------------------------------------------------------------------------
# IDOR y permisos: Contador Junior
# ---------------------------------------------------------------------------


def test_junior_no_crea_para_cliente_ajeno(client, usuario_junior, cliente, cliente_junior):
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("hallazgos:crear"))
    clientes_disponibles = list(respuesta.context["formulario"].fields["cliente"].queryset)
    assert clientes_disponibles == [cliente_junior]


def test_junior_consulta_hallazgo_ajeno_en_solo_lectura(client, usuario_junior, hallazgo_cliente):
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("hallazgos:detalle", args=[hallazgo_cliente.pk]))
    assert respuesta.status_code == 200
    assert respuesta.context["puede_gestionar"] is False
    contenido = respuesta.content.decode()
    assert reverse("hallazgos:editar", args=[hallazgo_cliente.pk]) not in contenido
    assert reverse("hallazgos:cambiar_estado", args=[hallazgo_cliente.pk]) not in contenido
    assert reverse("hallazgos:agregar_adjunto", args=[hallazgo_cliente.pk]) not in contenido


def test_junior_gestiona_el_detalle_de_su_propio_hallazgo(client, usuario_junior, hallazgo_cliente_junior):
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("hallazgos:detalle", args=[hallazgo_cliente_junior.pk]))
    assert respuesta.context["puede_gestionar"] is True
    assert reverse("hallazgos:editar", args=[hallazgo_cliente_junior.pk]) in respuesta.content.decode()


def test_junior_su_propio_hallazgo_carga(client, usuario_junior, hallazgo_cliente_junior):
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("hallazgos:detalle", args=[hallazgo_cliente_junior.pk]))
    assert respuesta.status_code == 200


def test_junior_edita_hallazgo_de_su_cliente(client, usuario_junior, hallazgo_cliente_junior):
    client.force_login(usuario_junior)
    datos = _datos_hallazgo(hallazgo_cliente_junior.cliente_id)
    datos["tipo_hallazgo"] = "Revisión periódica"
    respuesta = client.post(reverse("hallazgos:editar", args=[hallazgo_cliente_junior.pk]), datos)
    assert respuesta.status_code == 302
    hallazgo_cliente_junior.refresh_from_db()
    assert hallazgo_cliente_junior.tipo_hallazgo == "Revisión periódica"


def test_junior_no_edita_hallazgo_ajeno(client, usuario_junior, hallazgo_cliente):
    client.force_login(usuario_junior)
    datos = _datos_hallazgo(hallazgo_cliente.cliente_id)
    respuesta = client.post(reverse("hallazgos:editar", args=[hallazgo_cliente.pk]), datos)
    assert respuesta.status_code == 404


def test_junior_no_elimina_hallazgo(client, usuario_junior, hallazgo_cliente_junior):
    client.force_login(usuario_junior)
    respuesta = client.post(reverse("hallazgos:eliminar", args=[hallazgo_cliente_junior.pk]))
    assert respuesta.status_code == 403
    assert Hallazgo.objects.filter(pk=hallazgo_cliente_junior.pk).exists()


def test_senior_elimina_hallazgo_de_otro_usuario(client, usuario_senior, hallazgo_cliente):
    client.force_login(usuario_senior)
    respuesta = client.post(reverse("hallazgos:eliminar", args=[hallazgo_cliente.pk]))
    assert respuesta.status_code == 302
    assert not Hallazgo.objects.filter(pk=hallazgo_cliente.pk).exists()


# ---------------------------------------------------------------------------
# Cambio de estado
# ---------------------------------------------------------------------------


def test_cambiar_estado_a_cerrado_sin_observacion_no_cierra(client, usuario_administrador, hallazgo_cliente):
    client.force_login(usuario_administrador)
    client.post(
        reverse("hallazgos:cambiar_estado", args=[hallazgo_cliente.pk]),
        {"estado": Hallazgo.CERRADO, "observacion_cierre": ""},
    )
    hallazgo_cliente.refresh_from_db()
    assert hallazgo_cliente.estado != Hallazgo.CERRADO


def test_cambiar_estado_a_cerrado_con_observacion_cierra(client, usuario_administrador, hallazgo_cliente):
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("hallazgos:cambiar_estado", args=[hallazgo_cliente.pk]),
        {"estado": Hallazgo.CERRADO, "observacion_cierre": "Aclarado con el cliente."},
    )
    assert respuesta.status_code == 302
    hallazgo_cliente.refresh_from_db()
    assert hallazgo_cliente.estado == Hallazgo.CERRADO
    assert hallazgo_cliente.observacion_cierre == "Aclarado con el cliente."


def test_junior_cambia_estado_de_su_propio_hallazgo(client, usuario_junior, hallazgo_cliente_junior):
    client.force_login(usuario_junior)
    respuesta = client.post(
        reverse("hallazgos:cambiar_estado", args=[hallazgo_cliente_junior.pk]),
        {"estado": Hallazgo.EN_PROCESO, "observacion_cierre": ""},
    )
    assert respuesta.status_code == 302
    hallazgo_cliente_junior.refresh_from_db()
    assert hallazgo_cliente_junior.estado == Hallazgo.EN_PROCESO


def test_junior_no_cambia_estado_de_hallazgo_ajeno(client, usuario_junior, hallazgo_cliente):
    client.force_login(usuario_junior)
    respuesta = client.post(
        reverse("hallazgos:cambiar_estado", args=[hallazgo_cliente.pk]),
        {"estado": Hallazgo.EN_PROCESO, "observacion_cierre": ""},
    )
    assert respuesta.status_code == 404


# ---------------------------------------------------------------------------
# Adjuntos: agregar, descargar, eliminar, IDOR
# ---------------------------------------------------------------------------


def _archivo_prueba():
    return SimpleUploadedFile("soporte.pdf", b"%PDF-contenido", content_type="application/pdf")


def _subir_adjunto(client, hallazgo):
    """Sube un adjunto de prueba al hallazgo y devuelve la fila creada."""
    client.post(reverse("hallazgos:agregar_adjunto", args=[hallazgo.pk]), {"archivo": _archivo_prueba()})
    return Adjunto.objects.get(tabla_origen=Adjunto.HALLAZGO, id_origen=hallazgo.pk)


def test_agregar_adjunto(client, usuario_administrador, hallazgo_cliente):
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("hallazgos:agregar_adjunto", args=[hallazgo_cliente.pk]), {"archivo": _archivo_prueba()}
    )
    assert respuesta.status_code == 302
    assert Adjunto.objects.filter(tabla_origen=Adjunto.HALLAZGO, id_origen=hallazgo_cliente.pk).count() == 1


def test_descargar_adjunto_devuelve_archivo(client, usuario_administrador, hallazgo_cliente):
    client.force_login(usuario_administrador)
    adjunto = _subir_adjunto(client, hallazgo_cliente)

    respuesta = client.get(reverse("hallazgos:descargar_adjunto", args=[adjunto.pk]))
    assert respuesta.status_code == 200
    assert respuesta["Content-Disposition"].startswith("attachment;")
    assert b"".join(respuesta.streaming_content).startswith(b"%PDF")


def test_eliminar_adjunto(client, usuario_administrador, hallazgo_cliente):
    client.force_login(usuario_administrador)
    adjunto = _subir_adjunto(client, hallazgo_cliente)

    respuesta = client.post(reverse("hallazgos:eliminar_adjunto", args=[adjunto.pk]))
    assert respuesta.status_code == 302
    assert not Adjunto.objects.filter(pk=adjunto.pk).exists()


def test_junior_no_agrega_adjunto_a_hallazgo_ajeno(client, usuario_junior, hallazgo_cliente):
    client.force_login(usuario_junior)
    respuesta = client.post(
        reverse("hallazgos:agregar_adjunto", args=[hallazgo_cliente.pk]), {"archivo": _archivo_prueba()}
    )
    assert respuesta.status_code == 404


def test_junior_descarga_pero_no_elimina_adjunto_de_hallazgo_ajeno(
    client, usuario_administrador, usuario_junior, hallazgo_cliente
):
    client.force_login(usuario_administrador)
    adjunto = _subir_adjunto(client, hallazgo_cliente)

    client.force_login(usuario_junior)
    assert client.get(reverse("hallazgos:descargar_adjunto", args=[adjunto.pk])).status_code == 200
    assert client.post(reverse("hallazgos:eliminar_adjunto", args=[adjunto.pk])).status_code == 404


# ---------------------------------------------------------------------------
# Listado y filtros
# ---------------------------------------------------------------------------


def test_lista_filtra_por_tipo(client, usuario_administrador, hallazgo_cliente, hallazgo_cliente_junior):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("hallazgos:lista"), {"tipo": "Inconsistencia"})
    assert list(respuesta.context["hallazgos"]) == [hallazgo_cliente]


def test_lista_filtra_por_responsable(client, usuario_administrador, usuario_senior, cliente):
    otro = Hallazgo.objects.create(
        cliente=cliente,
        tipo_hallazgo="Revisión periódica",
        fecha_inicio_periodo=date(2026, 3, 1),
        fecha_fin_periodo=date(2026, 3, 31),
        responsable=usuario_senior,
        descripcion="Revisión trimestral.",
    )
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("hallazgos:lista"), {"responsable": usuario_senior.pk})
    assert list(respuesta.context["hallazgos"]) == [otro]


# ---------------------------------------------------------------------------
# Seguridad transversal
# ---------------------------------------------------------------------------


def test_post_sin_csrf_es_rechazado(client, usuario_administrador, cliente):
    from django.test import Client as ClienteSinCsrf

    cliente_http = ClienteSinCsrf(enforce_csrf_checks=True)
    cliente_http.force_login(usuario_administrador)
    respuesta = cliente_http.post(reverse("hallazgos:crear"), _datos_hallazgo(cliente.pk))
    assert respuesta.status_code == 403
