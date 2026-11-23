"""Pruebas de los servicios del módulo 4: expedición de documentos y certificados."""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image

from aplicaciones.documentos import servicios
from aplicaciones.documentos.formularios import CampoPlantillaFormSet, PlantillaForm
from aplicaciones.documentos.models import (
    CampoPlantilla,
    Documento,
    DocumentoDetalle,
    DocumentoValor,
    Plantilla,
)
from aplicaciones.seguridad.models import ConfiguracionDespacho

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_root_temporal(settings, tmp_path):
    """Redirige los archivos generados en las pruebas a un directorio temporal."""
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
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
def usuario_firmante(usuario_administrador):
    usuario_administrador.firma = _imagen_prueba()
    usuario_administrador.identificacion = "1032456789"
    usuario_administrador.numero_tarjeta_profesional = "123456-T"
    usuario_administrador.save()
    return usuario_administrador


@pytest.fixture
def plantilla_mixta():
    plantilla = Plantilla.objects.create(
        nombre_plantilla="Certificado mixto",
        tipo_documento="Certificado mixto",
        texto_predeterminado=(
            "{{ cliente }} - {{ concepto }}\n"
            "{% for fila in filas_repetibles %}{{ fila.accionista }} {{ fila.porcentaje }}%\n{% endfor %}"
        ),
    )
    campo_simple = CampoPlantilla.objects.create(
        plantilla=plantilla, nombre_campo="Concepto", tipo_campo=CampoPlantilla.SIMPLE
    )
    campo_accionista = CampoPlantilla.objects.create(
        plantilla=plantilla, nombre_campo="Accionista", tipo_campo=CampoPlantilla.REPETIBLE, es_repetible=True
    )
    campo_porcentaje = CampoPlantilla.objects.create(
        plantilla=plantilla, nombre_campo="Porcentaje", tipo_campo=CampoPlantilla.REPETIBLE, es_repetible=True
    )
    return plantilla, campo_simple, campo_accionista, campo_porcentaje


def test_generar_documento_crea_valores_detalles_y_pdf(
    cliente, plantilla_mixta, usuario_firmante, usuario_administrador, despacho
):
    plantilla, campo_simple, campo_accionista, campo_porcentaje = plantilla_mixta

    documento = servicios.generar_documento(
        cliente=cliente,
        plantilla=plantilla,
        periodo="2026",
        descripcion="Prueba",
        usuario_firmante=usuario_firmante,
        usuario_generador=usuario_administrador,
        valores_simples={campo_simple.pk: "Honorarios"},
        filas_repetibles=[
            {campo_accionista.pk: "Ana", campo_porcentaje.pk: "60"},
            {campo_accionista.pk: "Luis", campo_porcentaje.pk: "40"},
        ],
    )

    assert documento.pk is not None
    assert DocumentoValor.objects.filter(documento=documento).count() == 1
    assert DocumentoDetalle.objects.filter(documento=documento).count() == 4
    assert documento.archivo.name
    contenido = documento.archivo.read()
    assert contenido.startswith(b"%PDF")


def test_eliminar_documento_borra_archivo_y_registro(
    cliente, plantilla_mixta, usuario_firmante, usuario_administrador, despacho
):
    plantilla, campo_simple, _, _ = plantilla_mixta
    documento = servicios.generar_documento(
        cliente=cliente,
        plantilla=plantilla,
        periodo="2026",
        descripcion="",
        usuario_firmante=usuario_firmante,
        usuario_generador=usuario_administrador,
        valores_simples={campo_simple.pk: "Honorarios"},
        filas_repetibles=[],
    )
    ruta_archivo = documento.archivo.path
    import os

    assert os.path.exists(ruta_archivo)
    servicios.eliminar_documento(documento)
    assert not os.path.exists(ruta_archivo)
    assert not Documento.objects.filter(pk=documento.pk).exists()


def _datos_formset_vacio(prefix="campos"):
    return {
        f"{prefix}-TOTAL_FORMS": "0",
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


def test_crear_plantilla_guarda_plantilla_y_campos():
    datos = {"nombre_plantilla": "Nueva", "tipo_documento": "Nueva", "texto_predeterminado": "Texto"}
    datos.update(_datos_formset_vacio())
    datos.update(
        {
            "campos-TOTAL_FORMS": "1",
            "campos-0-nombre_campo": "Campo uno",
            "campos-0-tipo_campo": CampoPlantilla.SIMPLE,
        }
    )
    formulario = PlantillaForm(datos)
    formset = CampoPlantillaFormSet(datos, instance=Plantilla(), prefix="campos")
    assert formulario.is_valid(), formulario.errors
    assert formset.is_valid(), formset.errors

    plantilla = servicios.crear_plantilla(formulario, formset)
    assert plantilla.pk is not None
    assert plantilla.campos.count() == 1


def test_actualizar_plantilla_no_permite_borrar_campo_con_documentos(
    cliente, plantilla_mixta, usuario_firmante, usuario_administrador, despacho
):
    plantilla, campo_simple, campo_accionista, campo_porcentaje = plantilla_mixta
    servicios.generar_documento(
        cliente=cliente,
        plantilla=plantilla,
        periodo="2026",
        descripcion="",
        usuario_firmante=usuario_firmante,
        usuario_generador=usuario_administrador,
        valores_simples={campo_simple.pk: "Honorarios"},
        filas_repetibles=[],
    )

    datos = {
        "nombre_plantilla": plantilla.nombre_plantilla,
        "tipo_documento": plantilla.tipo_documento,
        "texto_predeterminado": plantilla.texto_predeterminado,
        "campos-TOTAL_FORMS": "3",
        "campos-INITIAL_FORMS": "3",
        "campos-MIN_NUM_FORMS": "0",
        "campos-MAX_NUM_FORMS": "1000",
        "campos-0-id_campo": campo_simple.pk,
        "campos-0-nombre_campo": campo_simple.nombre_campo,
        "campos-0-tipo_campo": campo_simple.tipo_campo,
        "campos-0-DELETE": "on",
        "campos-1-id_campo": campo_accionista.pk,
        "campos-1-nombre_campo": campo_accionista.nombre_campo,
        "campos-1-tipo_campo": campo_accionista.tipo_campo,
        "campos-2-id_campo": campo_porcentaje.pk,
        "campos-2-nombre_campo": campo_porcentaje.nombre_campo,
        "campos-2-tipo_campo": campo_porcentaje.tipo_campo,
    }
    formulario = PlantillaForm(datos, instance=plantilla)
    formset = CampoPlantillaFormSet(datos, instance=plantilla, prefix="campos")
    assert formulario.is_valid(), formulario.errors
    assert formset.is_valid(), formset.errors

    with pytest.raises(ValueError):
        servicios.actualizar_plantilla(plantilla, formulario, formset)

    assert CampoPlantilla.objects.filter(pk=campo_simple.pk).exists()


# ---------------------------------------------------------------------------
# Firma del contador en el PDF
# ---------------------------------------------------------------------------


def _firma(usuario, ancho, alto):
    buffer = io.BytesIO()
    PILImage.new("RGB", (ancho, alto), color="black").save(buffer, format="PNG")
    usuario.firma = SimpleUploadedFile("firma.png", buffer.getvalue(), content_type="image/png")
    usuario.save()
    return usuario


def test_la_firma_va_al_costado_izquierdo_sobre_los_datos_del_contador(usuario_firmante):
    bloque = servicios.bloque_firma(_firma(usuario_firmante, 400, 100), getSampleStyleSheet())

    firma, nombre, identificacion, tarjeta = bloque._content
    assert isinstance(firma, Image)
    assert firma.hAlign == "LEFT"
    assert [p.getPlainText() for p in (nombre, identificacion, tarjeta)] == [
        usuario_firmante.nombre,
        "C.C. 1032456789",
        "T.P. No. 123456-T",
    ]


def test_la_firma_se_escala_sin_deformarse(usuario_firmante):
    """Una firma ancha ocupa el ancho reservado; una alta, el alto; nunca se estira."""
    ancha = servicios.bloque_firma(_firma(usuario_firmante, 400, 100), getSampleStyleSheet())._content[0]
    assert ancha.drawWidth == pytest.approx(servicios.ANCHO_FIRMA)
    assert ancha.drawHeight == pytest.approx(servicios.ANCHO_FIRMA / 4)

    alta = servicios.bloque_firma(_firma(usuario_firmante, 100, 100), getSampleStyleSheet())._content[0]
    assert alta.drawHeight == pytest.approx(servicios.ALTO_FIRMA)
    assert alta.drawWidth == pytest.approx(servicios.ALTO_FIRMA)


def test_sin_firma_cargada_se_deja_el_espacio_para_firmar(usuario_administrador):
    bloque = servicios.bloque_firma(usuario_administrador, getSampleStyleSheet())
    assert not isinstance(bloque._content[0], Image)
    assert bloque._content[1].getPlainText() == usuario_administrador.nombre


# ---------------------------------------------------------------------------
# La firma va al final de la hoja (decisión del usuario, 22-nov-2026).
# ---------------------------------------------------------------------------


def _lienzo():
    from reportlab.pdfgen.canvas import Canvas

    return Canvas(io.BytesIO())


def test_espacio_hasta_el_final_deja_la_firma_pegada_al_margen_inferior():
    from reportlab.platypus import KeepTogether, Spacer

    firma = KeepTogether([Spacer(1, 30), Spacer(1, 20)])
    espacio = servicios.EspacioHastaElFinal(firma, minimo=10)
    _, alto = espacio.wrapOn(_lienzo(), 400, 500)
    assert alto == 500 - 50 - 1


def test_espacio_hasta_el_final_respeta_el_minimo_si_no_cabe():
    from reportlab.platypus import KeepTogether, Spacer

    firma = KeepTogether([Spacer(1, 30), Spacer(1, 20)])
    espacio = servicios.EspacioHastaElFinal(firma, minimo=40)
    _, alto = espacio.wrapOn(_lienzo(), 400, 60)
    assert alto == 40


def test_el_pdf_del_documento_sigue_en_una_hoja_con_la_firma_abajo(
    cliente, plantilla_mixta, usuario_firmante, usuario_administrador, despacho
):
    plantilla, campo_simple, campo_accionista, campo_porcentaje = plantilla_mixta
    documento = servicios.generar_documento(
        cliente=cliente,
        plantilla=plantilla,
        periodo="2026",
        descripcion="Prueba",
        usuario_firmante=usuario_firmante,
        usuario_generador=usuario_administrador,
        valores_simples={campo_simple.pk: "Honorarios"},
        filas_repetibles=[{campo_accionista.pk: "Ana", campo_porcentaje.pk: "60"}],
    )
    contenido = documento.archivo.read()
    # Una sola hoja: el espacio no empuja la firma a una página nueva.
    assert contenido.count(b"/Type /Page\n") + contenido.count(b"/Type /Page ") == 1
