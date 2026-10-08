"""Pruebas de los selectores del módulo 4: expedición de documentos y certificados."""

from datetime import date

import pytest

from aplicaciones.documentos import selectores
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


@pytest.mark.parametrize(
    "nombre_campo, esperado",
    [
        ("Concepto", "concepto"),
        ("Valor del ingreso certificado", "valor_del_ingreso_certificado"),
        ("Ciudad donde se consignó la retención", "ciudad_donde_se_consigno_la_retencion"),
        ("Nombre del accionista", "nombre_del_accionista"),
    ],
)
def test_clave_variable_campo(nombre_campo, esperado):
    assert selectores.clave_variable_campo(nombre_campo) == esperado


@pytest.fixture
def plantilla_simple():
    plantilla = Plantilla.objects.create(
        nombre_plantilla="Certificado simple",
        tipo_documento="Certificado simple",
        texto_predeterminado="{{ cliente }} certifica {{ concepto }} el {{ fecha_expedicion }}.",
    )
    CampoPlantilla.objects.create(
        plantilla=plantilla, nombre_campo="Concepto", tipo_campo=CampoPlantilla.SIMPLE
    )
    return plantilla


@pytest.fixture
def plantilla_repetible():
    plantilla = Plantilla.objects.create(
        nombre_plantilla="Certificado repetible",
        tipo_documento="Certificado repetible",
        texto_predeterminado=(
            "{{ cliente }}:\n"
            "{% for fila in filas_repetibles %}- {{ fila.nombre }}: {{ fila.porcentaje }}%\n{% endfor %}"
        ),
    )
    CampoPlantilla.objects.create(
        plantilla=plantilla, nombre_campo="Nombre", tipo_campo=CampoPlantilla.REPETIBLE, es_repetible=True
    )
    CampoPlantilla.objects.create(
        plantilla=plantilla, nombre_campo="Porcentaje", tipo_campo=CampoPlantilla.REPETIBLE, es_repetible=True
    )
    return plantilla


@pytest.fixture
def despacho(db):
    return ConfiguracionDespacho.objects.create(
        pk=1, nombre_despacho="Befrec Y Asociados SAS", ciudad="Bogotá D.C."
    )


def test_clientes_para_generar_junior_solo_ve_los_propios(usuario_junior, cliente, cliente_junior):
    clientes = selectores.clientes_para_generar(usuario_junior)
    assert list(clientes) == [cliente_junior]


def test_clientes_para_generar_admin_ve_todos(usuario_administrador, cliente, cliente_junior):
    clientes = selectores.clientes_para_generar(usuario_administrador)
    assert cliente in clientes and cliente_junior in clientes


def test_firmantes_disponibles_excluye_usuarios_sin_firma(
    usuario_administrador, usuario_senior, usuario_junior
):
    assert list(selectores.firmantes_disponibles()) == []

    from django.core.files.uploadedfile import SimpleUploadedFile

    usuario_administrador.firma = SimpleUploadedFile(
        "firma.png", b"contenido-imagen", content_type="image/png"
    )
    usuario_administrador.save()

    disponibles = selectores.firmantes_disponibles()
    assert usuario_administrador in disponibles
    assert usuario_junior not in disponibles


@pytest.fixture
def documento_generado(cliente, plantilla_simple, usuario_administrador, despacho):
    documento = Documento.objects.create(
        cliente=cliente, plantilla=plantilla_simple, periodo="2026", usuario_generador=usuario_administrador
    )
    campo = plantilla_simple.campos.get(nombre_campo="Concepto")
    DocumentoValor.objects.create(documento=documento, campo=campo, valor="<script>alert(1)</script>")
    return documento


def test_documentos_visibles_junior_ve_los_de_todos_los_clientes(
    usuario_junior, cliente_junior, cliente, plantilla_simple, usuario_administrador
):
    Documento.objects.create(
        cliente=cliente_junior, plantilla=plantilla_simple, usuario_generador=usuario_administrador
    )
    Documento.objects.create(
        cliente=cliente, plantilla=plantilla_simple, usuario_generador=usuario_administrador
    )

    visibles = selectores.documentos_visibles(usuario_junior)
    assert {d.cliente for d in visibles} == {cliente, cliente_junior}


def test_filtrar_historico_por_plantilla_y_rango_de_fechas(usuario_administrador, cliente, plantilla_simple):
    documento = Documento.objects.create(
        cliente=cliente, plantilla=plantilla_simple, usuario_generador=usuario_administrador
    )

    assert list(selectores.filtrar_historico(usuario_administrador, plantilla=plantilla_simple)) == [
        documento
    ]
    assert list(selectores.filtrar_historico(usuario_administrador, desde=date(2000, 1, 1))) == [documento]
    assert list(selectores.filtrar_historico(usuario_administrador, hasta=date(2000, 1, 1))) == []


def test_texto_certificado_renderizado_escapa_valores(documento_generado):
    texto = selectores.texto_certificado_renderizado(documento_generado)
    assert "<script>" not in texto
    assert "&lt;script&gt;" in texto


def test_texto_certificado_renderizado_agrupa_filas_repetibles(
    cliente, plantilla_repetible, usuario_administrador, despacho
):
    documento = Documento.objects.create(
        cliente=cliente, plantilla=plantilla_repetible, usuario_generador=usuario_administrador
    )
    campo_nombre = plantilla_repetible.campos.get(nombre_campo="Nombre")
    campo_porcentaje = plantilla_repetible.campos.get(nombre_campo="Porcentaje")
    DocumentoDetalle.objects.create(documento=documento, campo=campo_nombre, fila=1, valor="Ana")
    DocumentoDetalle.objects.create(documento=documento, campo=campo_porcentaje, fila=1, valor="60")
    DocumentoDetalle.objects.create(documento=documento, campo=campo_nombre, fila=2, valor="Luis")
    DocumentoDetalle.objects.create(documento=documento, campo=campo_porcentaje, fila=2, valor="40")

    texto = selectores.texto_certificado_renderizado(documento)
    assert "Ana: 60%" in texto
    assert "Luis: 40%" in texto


def test_contexto_previsualizacion_usa_id_campo_como_llave(plantilla_simple, cliente, despacho):
    campo = plantilla_simple.campos.get(nombre_campo="Concepto")
    contexto = selectores.contexto_previsualizacion(
        cliente=cliente,
        periodo="2026",
        descripcion="",
        valores_simples={campo.pk: "Honorarios"},
        filas_repetibles=[],
    )
    assert contexto["concepto"] == "Honorarios"
    assert contexto["cliente"] == cliente.nombre_razon_social
