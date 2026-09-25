"""Pruebas de vistas, permisos y seguridad del módulo 4: expedición de documentos y certificados."""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image as PILImage

from aplicaciones.documentos.models import CampoPlantilla, Documento, Plantilla
from aplicaciones.seguridad.models import ConfiguracionDespacho, PermisoRolModulo

pytestmark = pytest.mark.django_db

URLS_PROTEGIDAS = [
    "documentos:historico",
    "documentos:generar",
    "documentos:mi_firma",
    "documentos:datos_despacho",
    "documentos:plantillas",
    "documentos:plantilla_crear",
]


@pytest.fixture(autouse=True)
def media_root_temporal(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture(autouse=True)
def despacho(db):
    return ConfiguracionDespacho.objects.create(
        pk=1, nombre_despacho="Befrec Y Asociados SAS", ciudad="Bogotá D.C."
    )


def _imagen_prueba():
    buffer = io.BytesIO()
    PILImage.new("RGB", (10, 10), color="black").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile("firma.png", buffer.read(), content_type="image/png")


@pytest.fixture
def firmante(usuario_administrador):
    usuario_administrador.firma = _imagen_prueba()
    usuario_administrador.numero_tarjeta_profesional = "123456-T"
    usuario_administrador.save()
    return usuario_administrador


@pytest.fixture
def plantilla_simple():
    plantilla = Plantilla.objects.create(
        nombre_plantilla="Certificado simple",
        tipo_documento="Certificado simple",
        texto_predeterminado=(
            "{{ cliente }} certifica {{ concepto }} el {{ fecha_expedicion }}. {{ descripcion }}"
        ),
    )
    CampoPlantilla.objects.create(
        plantilla=plantilla, nombre_campo="Concepto", tipo_campo=CampoPlantilla.SIMPLE
    )
    return plantilla


@pytest.fixture
def documento_cliente(cliente, plantilla_simple, usuario_administrador):
    return Documento.objects.create(
        cliente=cliente, plantilla=plantilla_simple, usuario_generador=usuario_administrador
    )


@pytest.fixture
def documento_cliente_junior(cliente_junior, plantilla_simple, usuario_administrador):
    return Documento.objects.create(
        cliente=cliente_junior, plantilla=plantilla_simple, usuario_generador=usuario_administrador
    )


def _campo_id(plantilla_simple):
    return plantilla_simple.campos.get(nombre_campo="Concepto").pk


# ---------------------------------------------------------------------------
# Acceso sin sesión / módulo inhabilitado
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nombre_url", URLS_PROTEGIDAS)
def test_urls_requieren_sesion(client, nombre_url):
    respuesta = client.get(reverse(nombre_url))
    assert respuesta.status_code == 302
    assert reverse("seguridad:iniciar_sesion") in respuesta.url


def test_historico_requiere_modulo_habilitado(client, usuario_administrador, modulo_documentos):
    PermisoRolModulo.objects.create(rol=usuario_administrador.rol, modulo=modulo_documentos, habilitado=False)
    client.force_login(usuario_administrador)
    assert client.get(reverse("documentos:historico")).status_code == 403


# ---------------------------------------------------------------------------
# Flujo completo: generar -> previsualizar -> confirmar
# ---------------------------------------------------------------------------


def test_flujo_generar_confirmar_crea_documento_con_pdf(
    client, usuario_administrador, cliente, plantilla_simple, firmante
):
    client.force_login(usuario_administrador)

    respuesta = client.post(
        reverse("documentos:generar"),
        {
            "cliente": cliente.pk,
            "plantilla": plantilla_simple.pk,
            "periodo": "2026",
            "descripcion": "<script>alert(1)</script>",
            "usuario_firmante": firmante.pk,
            f"campo_{_campo_id(plantilla_simple)}": "Honorarios",
        },
    )
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("documentos:confirmar")

    respuesta_preview = client.get(reverse("documentos:confirmar"))
    assert respuesta_preview.status_code == 200
    contenido_preview = respuesta_preview.content.decode()
    assert "<script>alert(1)</script>" not in contenido_preview
    assert "&lt;script&gt;" in contenido_preview

    respuesta_confirmar = client.post(reverse("documentos:confirmar"))
    assert respuesta_confirmar.status_code == 302

    documento = Documento.objects.get(cliente=cliente, plantilla=plantilla_simple)
    assert respuesta_confirmar.url == reverse("documentos:detalle", args=[documento.pk])
    assert documento.valores.count() == 1
    assert documento.archivo.name
    assert documento.archivo.read().startswith(b"%PDF")
    assert "documento_pendiente" not in client.session


def test_generar_sin_firma_disponible_no_ofrece_firmantes(client, usuario_administrador, cliente):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("documentos:generar"))
    assert respuesta.status_code == 200
    assert list(respuesta.context["formulario"].fields["usuario_firmante"].queryset) == []


def test_confirmar_sin_datos_en_sesion_redirige_a_generar(client, usuario_administrador):
    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("documentos:confirmar"))
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("documentos:generar")


# ---------------------------------------------------------------------------
# IDOR: Contador Junior
# ---------------------------------------------------------------------------


def test_junior_no_genera_para_cliente_ajeno(
    client, usuario_junior, cliente, cliente_junior, plantilla_simple, firmante
):
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("documentos:generar"))
    clientes_disponibles = list(respuesta.context["formulario"].fields["cliente"].queryset)
    assert clientes_disponibles == [cliente_junior]
    assert cliente not in clientes_disponibles


def test_junior_detalle_documento_ajeno_devuelve_404(client, usuario_junior, documento_cliente):
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("documentos:detalle", args=[documento_cliente.pk]))
    assert respuesta.status_code == 404


def test_junior_descarga_documento_ajeno_devuelve_404(client, usuario_junior, documento_cliente):
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("documentos:descargar", args=[documento_cliente.pk]))
    assert respuesta.status_code == 404


def test_junior_su_propio_documento_carga(client, usuario_junior, documento_cliente_junior):
    client.force_login(usuario_junior)
    respuesta = client.get(reverse("documentos:detalle", args=[documento_cliente_junior.pk]))
    assert respuesta.status_code == 200


# ---------------------------------------------------------------------------
# Roles: plantillas, mi firma, eliminar
# ---------------------------------------------------------------------------


def test_junior_no_accede_a_gestion_plantillas(client, usuario_junior):
    client.force_login(usuario_junior)
    assert client.get(reverse("documentos:plantillas")).status_code == 403


def test_senior_no_accede_a_gestion_plantillas(client, usuario_senior):
    client.force_login(usuario_senior)
    assert client.get(reverse("documentos:plantillas")).status_code == 403


def test_junior_no_accede_a_mi_firma(client, usuario_junior):
    client.force_login(usuario_junior)
    assert client.get(reverse("documentos:mi_firma")).status_code == 403


def test_senior_accede_a_mi_firma(client, usuario_senior):
    client.force_login(usuario_senior)
    assert client.get(reverse("documentos:mi_firma")).status_code == 200


@pytest.mark.parametrize("usuario_fixture", ["usuario_junior", "usuario_senior"])
def test_solo_administrador_accede_a_datos_del_despacho(client, request, usuario_fixture):
    client.force_login(request.getfixturevalue(usuario_fixture))
    assert client.get(reverse("documentos:datos_despacho")).status_code == 403


def test_administrador_carga_membrete_del_despacho(client, usuario_administrador, despacho):
    client.force_login(usuario_administrador)
    imagen = _imagen_prueba()
    imagen.name = "membrete.png"
    respuesta = client.post(
        reverse("documentos:datos_despacho"),
        {
            "nombre_despacho": "Befrec Y Asociados SAS",
            "nit_despacho": "900123456-1",
            "membrete": imagen,
            "ciudad": "Bogotá D.C.",
            "direccion": "",
            "telefono": "",
            "correo": "",
        },
    )
    assert respuesta.status_code == 302
    despacho.refresh_from_db()
    assert despacho.nit_despacho == "900123456-1"
    assert despacho.membrete.name.startswith("despacho/")


def test_historico_muestra_datos_del_despacho_solo_al_administrador(
    client, usuario_administrador, usuario_senior
):
    url_despacho = reverse("documentos:datos_despacho")
    client.force_login(usuario_administrador)
    assert url_despacho in client.get(reverse("documentos:historico")).content.decode()
    client.force_login(usuario_senior)
    assert url_despacho not in client.get(reverse("documentos:historico")).content.decode()


def test_junior_no_elimina_documento(client, usuario_junior, documento_cliente_junior):
    client.force_login(usuario_junior)
    respuesta = client.post(reverse("documentos:eliminar", args=[documento_cliente_junior.pk]))
    assert respuesta.status_code == 403
    assert Documento.objects.filter(pk=documento_cliente_junior.pk).exists()


def test_senior_elimina_documento_de_otro_usuario(client, usuario_senior, documento_cliente):
    client.force_login(usuario_senior)
    respuesta = client.post(reverse("documentos:eliminar", args=[documento_cliente.pk]))
    assert respuesta.status_code == 302
    assert not Documento.objects.filter(pk=documento_cliente.pk).exists()


# ---------------------------------------------------------------------------
# Gestión de plantillas (Administrador)
# ---------------------------------------------------------------------------


def test_admin_crea_plantilla_con_formset_de_campos(client, usuario_administrador):
    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("documentos:plantilla_crear"),
        {
            "nombre_plantilla": "Plantilla nueva",
            "tipo_documento": "Plantilla nueva",
            "texto_predeterminado": "Texto de prueba",
            "campos-TOTAL_FORMS": "1",
            "campos-INITIAL_FORMS": "0",
            "campos-MIN_NUM_FORMS": "0",
            "campos-MAX_NUM_FORMS": "1000",
            "campos-0-nombre_campo": "Campo nuevo",
            "campos-0-tipo_campo": CampoPlantilla.SIMPLE,
        },
    )
    assert respuesta.status_code == 302
    plantilla = Plantilla.objects.get(nombre_plantilla="Plantilla nueva")
    assert plantilla.campos.count() == 1


def test_editar_plantilla_no_permite_borrar_campo_con_documentos(
    client, usuario_administrador, documento_cliente, plantilla_simple
):
    campo = plantilla_simple.campos.get(nombre_campo="Concepto")
    from aplicaciones.documentos.models import DocumentoValor

    DocumentoValor.objects.create(documento=documento_cliente, campo=campo, valor="Algo")

    client.force_login(usuario_administrador)
    respuesta = client.post(
        reverse("documentos:plantilla_editar", args=[plantilla_simple.pk]),
        {
            "nombre_plantilla": plantilla_simple.nombre_plantilla,
            "tipo_documento": plantilla_simple.tipo_documento,
            "texto_predeterminado": plantilla_simple.texto_predeterminado,
            "campos-TOTAL_FORMS": "1",
            "campos-INITIAL_FORMS": "1",
            "campos-MIN_NUM_FORMS": "0",
            "campos-MAX_NUM_FORMS": "1000",
            "campos-0-id_campo": campo.pk,
            "campos-0-nombre_campo": campo.nombre_campo,
            "campos-0-tipo_campo": campo.tipo_campo,
            "campos-0-DELETE": "on",
        },
    )
    assert respuesta.status_code == 200
    assert CampoPlantilla.objects.filter(pk=campo.pk).exists()


# ---------------------------------------------------------------------------
# Histórico
# ---------------------------------------------------------------------------


def test_historico_filtra_por_plantilla(client, usuario_administrador, documento_cliente, cliente):
    otra_plantilla = Plantilla.objects.create(nombre_plantilla="Otra", tipo_documento="Otra")
    Documento.objects.create(
        cliente=cliente, plantilla=otra_plantilla, usuario_generador=usuario_administrador
    )

    client.force_login(usuario_administrador)
    respuesta = client.get(reverse("documentos:historico"), {"plantilla": documento_cliente.plantilla_id})
    documentos = list(respuesta.context["documentos"])
    assert documentos == [documento_cliente]


# ---------------------------------------------------------------------------
# Descarga
# ---------------------------------------------------------------------------


def test_descargar_documento_devuelve_pdf(client, usuario_administrador, cliente, plantilla_simple, firmante):
    client.force_login(usuario_administrador)
    from aplicaciones.documentos import servicios

    documento = servicios.generar_documento(
        cliente=cliente,
        plantilla=plantilla_simple,
        periodo="2026",
        descripcion="",
        usuario_firmante=firmante,
        usuario_generador=usuario_administrador,
        valores_simples={_campo_id(plantilla_simple): "Honorarios"},
        filas_repetibles=[],
    )
    respuesta = client.get(reverse("documentos:descargar", args=[documento.pk]))
    assert respuesta.status_code == 200
    assert respuesta["Content-Disposition"].startswith("attachment;")
    assert b"".join(respuesta.streaming_content).startswith(b"%PDF")


# ---------------------------------------------------------------------------
# Seguridad transversal
# ---------------------------------------------------------------------------


def test_post_sin_csrf_es_rechazado(client, usuario_administrador, cliente, plantilla_simple, firmante):
    from django.test import Client as ClienteSinCsrf

    cliente_http = ClienteSinCsrf(enforce_csrf_checks=True)
    cliente_http.force_login(usuario_administrador)
    respuesta = cliente_http.post(
        reverse("documentos:generar"),
        {
            "cliente": cliente.pk,
            "plantilla": plantilla_simple.pk,
            "periodo": "2026",
            "usuario_firmante": firmante.pk,
            f"campo_{_campo_id(plantilla_simple)}": "Honorarios",
        },
    )
    assert respuesta.status_code == 403
