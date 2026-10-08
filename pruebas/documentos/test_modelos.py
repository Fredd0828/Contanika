"""Pruebas de los modelos del módulo 4: expedición de documentos y certificados."""

import pytest
from django.db import IntegrityError, transaction

from aplicaciones.documentos.models import (
    CampoPlantilla,
    Documento,
    DocumentoDetalle,
    DocumentoValor,
    Plantilla,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_root_temporal(settings, tmp_path):
    """Redirige los archivos generados en las pruebas a un directorio temporal."""
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def plantilla():
    return Plantilla.objects.create(
        nombre_plantilla="Certificado de prueba",
        tipo_documento="Certificado de prueba",
        texto_predeterminado="Se certifica a {{ cliente }} por {{ concepto }}.",
    )


@pytest.fixture
def campo_concepto(plantilla):
    return CampoPlantilla.objects.create(
        plantilla=plantilla, nombre_campo="Concepto", tipo_campo=CampoPlantilla.SIMPLE
    )


@pytest.fixture
def documento(cliente, plantilla, usuario_administrador):
    return Documento.objects.create(
        cliente=cliente,
        plantilla=plantilla,
        periodo="2026",
        usuario_generador=usuario_administrador,
    )


def test_str_plantilla(plantilla):
    assert str(plantilla) == "Certificado de prueba"


def test_str_campo_plantilla(campo_concepto):
    assert str(campo_concepto) == "Concepto (Simple)"


def test_str_documento(documento):
    assert str(documento) == f"Certificado de prueba - {documento.cliente.nombre_razon_social}"


def test_archivo_usa_la_ruta_de_subida_configurada(documento):
    from django.core.files.base import ContentFile

    documento.archivo.save("prueba.pdf", ContentFile(b"%PDF-1.4 contenido"), save=True)
    assert documento.archivo.name.startswith("documentos/")
    assert documento.archivo.name.endswith(".pdf")


def test_periodo_es_opcional(cliente, plantilla, usuario_administrador):
    documento = Documento.objects.create(
        cliente=cliente, plantilla=plantilla, usuario_generador=usuario_administrador
    )
    assert documento.periodo == ""


def test_campo_plantilla_nombre_unico_por_plantilla(plantilla, campo_concepto):
    with pytest.raises(IntegrityError), transaction.atomic():
        CampoPlantilla.objects.create(
            plantilla=plantilla, nombre_campo="Concepto", tipo_campo=CampoPlantilla.SIMPLE
        )


def test_documento_valor_unico_por_documento_y_campo(documento, campo_concepto):
    DocumentoValor.objects.create(documento=documento, campo=campo_concepto, valor="Primer valor")
    with pytest.raises(IntegrityError), transaction.atomic():
        DocumentoValor.objects.create(documento=documento, campo=campo_concepto, valor="Segundo valor")


def test_str_documento_detalle(documento, campo_concepto):
    detalle = DocumentoDetalle.objects.create(documento=documento, campo=campo_concepto, fila=1, valor="30%")
    assert str(detalle) == "Concepto fila 1: 30%"
