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


def test_documentos_del_cliente_solo_trae_los_suyos_y_respeta_el_limite(
    usuario_administrador, cliente, cliente_junior, plantilla_simple
):
    for _ in range(3):
        Documento.objects.create(
            cliente=cliente, plantilla=plantilla_simple, usuario_generador=usuario_administrador
        )
    Documento.objects.create(
        cliente=cliente_junior, plantilla=plantilla_simple, usuario_generador=usuario_administrador
    )

    documentos = list(selectores.documentos_del_cliente(usuario_administrador, cliente, limite=2))
    assert len(documentos) == 2
    assert {documento.cliente for documento in documentos} == {cliente}


# ---------------------------------------------------------------------------
# La descripción anotada al generar el documento debe salir en el texto
# (vista previa, detalle y PDF), aunque la plantilla no tenga el marcador.
# ---------------------------------------------------------------------------


def test_texto_incluye_descripcion_aunque_la_plantilla_no_la_nombre(
    cliente, plantilla_simple, usuario_administrador, despacho
):
    documento = Documento.objects.create(
        cliente=cliente,
        plantilla=plantilla_simple,
        usuario_generador=usuario_administrador,
        descripcion="Se expide para trámite <bancario>.",
    )
    texto = selectores.texto_certificado_renderizado(documento)
    assert "Se expide para trámite &lt;bancario&gt;." in texto


def test_texto_no_repite_la_descripcion_si_la_plantilla_ya_la_usa(cliente, usuario_administrador, despacho):
    plantilla = Plantilla.objects.create(
        nombre_plantilla="Con descripción",
        tipo_documento="Con descripción",
        texto_predeterminado="{{ cliente }}. Nota: {{ descripcion }}",
    )
    documento = Documento.objects.create(
        cliente=cliente, plantilla=plantilla, usuario_generador=usuario_administrador, descripcion="Única"
    )
    assert selectores.texto_certificado_renderizado(documento).count("Única") == 1


def _documento_con_texto(cliente, usuario, texto, descripcion):
    plantilla = Plantilla.objects.create(
        nombre_plantilla="Prueba de orden", tipo_documento="Prueba de orden", texto_predeterminado=texto
    )
    return Documento.objects.create(
        cliente=cliente, plantilla=plantilla, usuario_generador=usuario, descripcion=descripcion
    )


def test_descripcion_va_antes_del_parrafo_de_expedicion(cliente, usuario_administrador, despacho):
    """Decisión del usuario (22-nov-2026): la descripción antes de «Se expide…»."""
    documento = _documento_con_texto(
        cliente,
        usuario_administrador,
        "Se certifica que {{ cliente }} existe.\n\nSe expide la presente en Bogotá.",
        "Para trámite bancario.",
    )
    texto = selectores.texto_certificado_renderizado(documento)
    assert texto.index("existe.") < texto.index("Para trámite bancario.") < texto.index("Se expide")
    assert "Para trámite bancario.<br/><br/>Se expide" in texto


def test_descripcion_antes_de_la_expedicion_despues_de_una_lista(cliente, usuario_administrador, despacho):
    """Como en la composición accionaria: la expedición sigue a un `{% endfor %}`."""
    documento = _documento_con_texto(
        cliente,
        usuario_administrador,
        "Socios:\n\n{% for fila in filas_repetibles %}- x\n{% endfor %}"
        "Se expide la presente certificación en Bogotá.",
        "Nota final.",
    )
    texto = selectores.texto_certificado_renderizado(documento)
    assert texto.index("Nota final.") < texto.index("Se expide")
    assert "<br/>Nota final.<br/><br/>Se expide" in texto


def test_descripcion_usa_la_ultima_mencion_de_expedicion(cliente, usuario_administrador, despacho):
    documento = _documento_con_texto(
        cliente,
        usuario_administrador,
        "Esta certificación se expide a solicitud.\n\nOtro párrafo.\n\nSe expide en Bogotá.",
        "Descripción.",
    )
    texto = selectores.texto_certificado_renderizado(documento)
    assert texto.index("Otro párrafo.") < texto.index("Descripción.") < texto.index("Se expide en")


def test_descripcion_al_final_si_la_plantilla_no_dice_expide(cliente, usuario_administrador, despacho):
    documento = _documento_con_texto(cliente, usuario_administrador, "Texto sin cierre.", "Al final.")
    assert selectores.texto_certificado_renderizado(documento).endswith("Al final.")


def test_texto_sin_descripcion_no_agrega_nada(cliente, plantilla_simple, usuario_administrador, despacho):
    documento = Documento.objects.create(
        cliente=cliente, plantilla=plantilla_simple, usuario_generador=usuario_administrador
    )
    assert not selectores.texto_certificado_renderizado(documento).endswith("<br/>")
