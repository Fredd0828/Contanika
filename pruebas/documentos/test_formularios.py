"""Pruebas de los formularios del módulo 4: expedición de documentos y certificados."""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage

from aplicaciones.documentos.formularios import (
    GenerarDocumentoForm,
    MiFirmaForm,
    construir_formset_filas_repetibles,
    construir_formulario_campos_simples,
    valores_desde_cleaned_data,
)
from aplicaciones.documentos.models import CampoPlantilla, Plantilla

pytestmark = pytest.mark.django_db


@pytest.fixture
def plantilla_simple():
    plantilla = Plantilla.objects.create(
        nombre_plantilla="Certificado simple", tipo_documento="Certificado simple"
    )
    CampoPlantilla.objects.create(
        plantilla=plantilla, nombre_campo="Concepto", tipo_campo=CampoPlantilla.SIMPLE
    )
    CampoPlantilla.objects.create(
        plantilla=plantilla, nombre_campo="Valor certificado", tipo_campo=CampoPlantilla.SIMPLE
    )
    return plantilla


@pytest.fixture
def plantilla_sin_campos():
    return Plantilla.objects.create(nombre_plantilla="Sin campos", tipo_documento="Sin campos")


def test_construir_formulario_campos_simples_un_campo_por_cada_campo_plantilla(plantilla_simple):
    formulario = construir_formulario_campos_simples(plantilla_simple)
    ids_esperados = set(plantilla_simple.campos.values_list("pk", flat=True))
    ids_formulario = {int(nombre.removeprefix("campo_")) for nombre in formulario.fields}
    assert ids_formulario == ids_esperados


def test_construir_formset_filas_repetibles_none_sin_campos_repetibles(plantilla_simple):
    assert construir_formset_filas_repetibles(plantilla_simple) is None


def test_construir_formset_filas_repetibles_con_campos():
    plantilla = Plantilla.objects.create(nombre_plantilla="Con filas", tipo_documento="Con filas")
    CampoPlantilla.objects.create(
        plantilla=plantilla, nombre_campo="Accionista", tipo_campo=CampoPlantilla.REPETIBLE, es_repetible=True
    )
    formset = construir_formset_filas_repetibles(plantilla)
    assert formset is not None
    assert formset.forms[0].fields


def test_valores_desde_cleaned_data_convierte_llaves_a_id_campo():
    datos = {"campo_5": "Uno", "campo_9": "Dos", "DELETE": False}
    assert valores_desde_cleaned_data(datos) == {5: "Uno", 9: "Dos"}


def test_generar_documento_form_restringe_cliente_para_junior(usuario_junior, cliente, cliente_junior):
    formulario = GenerarDocumentoForm(usuario=usuario_junior)
    clientes = list(formulario.fields["cliente"].queryset)
    assert clientes == [cliente_junior]


def test_generar_documento_form_admin_ve_todos_los_clientes(usuario_administrador, cliente, cliente_junior):
    formulario = GenerarDocumentoForm(usuario=usuario_administrador)
    clientes = set(formulario.fields["cliente"].queryset)
    assert {cliente, cliente_junior} <= clientes


def _imagen_prueba(tamano_bytes=None):
    buffer = io.BytesIO()
    PILImage.new("RGB", (10, 10), color="black").save(buffer, format="PNG")
    contenido = buffer.getvalue()
    if tamano_bytes:
        contenido += b"0" * tamano_bytes
    return SimpleUploadedFile("firma.png", contenido, content_type="image/png")


def test_mi_firma_form_rechaza_archivo_mayor_a_2mb():
    formulario = MiFirmaForm(
        data={"identificacion": "123", "numero_tarjeta_profesional": "T-1"},
        files={"firma": _imagen_prueba(tamano_bytes=3 * 1024 * 1024)},
    )
    assert not formulario.is_valid()
    assert "firma" in formulario.errors


def test_mi_firma_form_acepta_imagen_valida():
    formulario = MiFirmaForm(
        data={"identificacion": "123", "numero_tarjeta_profesional": "T-1"},
        files={"firma": _imagen_prueba()},
    )
    assert formulario.is_valid(), formulario.errors
