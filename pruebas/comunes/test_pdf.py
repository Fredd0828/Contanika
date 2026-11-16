"""Pruebas de la hoja común de los PDF (franja, encabezado, tablas y pie paginado)."""

from types import SimpleNamespace

import pytest
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, Table

from aplicaciones.comunes import paleta, pdf


@pytest.fixture
def despacho():
    return SimpleNamespace(
        nombre_despacho="Despacho de Prueba",
        nit_despacho="900123456",
        direccion="Calle 1 # 2-3",
        ciudad="Bogotá D.C.",
        telefono="3001234567",
        correo="despacho@ejemplo.co",
        membrete=None,
    )


@pytest.fixture
def textos_del_pie(monkeypatch):
    """Guarda lo que el lienzo escribe en el pie de cada página."""
    escritos = {"derecha": [], "izquierda": []}

    def a_la_derecha(lienzo, x, y, texto, *args, **kwargs):
        escritos["derecha"].append(texto)

    def a_la_izquierda(lienzo, x, y, texto, *args, **kwargs):
        escritos["izquierda"].append(texto)

    monkeypatch.setattr(pdf._LienzoConPie, "drawRightString", a_la_derecha)
    monkeypatch.setattr(pdf._LienzoConPie, "drawString", a_la_izquierda)
    return escritos


def test_datos_del_despacho_omiten_los_vacios(despacho):
    despacho.telefono = ""
    datos = pdf._datos_despacho(despacho)
    assert datos == "NIT 900123456 · Calle 1 # 2-3 · Bogotá D.C. · despacho@ejemplo.co"
    assert pdf._datos_despacho(None) == ""


def test_construir_pdf_numera_las_paginas(despacho, textos_del_pie):
    estilos = pdf.estilos_documento()
    elementos = [
        Paragraph("Primera", estilos["normal"]),
        PageBreak(),
        Paragraph("Segunda", estilos["normal"]),
    ]
    contenido = pdf.construir_pdf(elementos, tamano=A4, titulo="Prueba", despacho=despacho)
    assert contenido.startswith(b"%PDF")
    assert textos_del_pie["derecha"] == ["Página 1 de 2", "Página 2 de 2"]
    assert textos_del_pie["izquierda"][0].startswith("Despacho de Prueba · NIT 900123456")


def test_el_pie_se_recorta_si_no_cabe(despacho, textos_del_pie):
    despacho.direccion = "Dirección muy larga " * 20
    estilos = pdf.estilos_documento()
    pdf.construir_pdf([Paragraph("Texto", estilos["normal"])], tamano=A4, titulo="Prueba", despacho=despacho)
    pie = textos_del_pie["izquierda"][0]
    assert pie.endswith("…")
    assert len(pie) < len(despacho.direccion)


def test_construir_pdf_sin_despacho(textos_del_pie):
    estilos = pdf.estilos_documento()
    contenido = pdf.construir_pdf(
        [Paragraph("Texto", estilos["normal"])], tamano=A4, titulo="Prueba", despacho=None
    )
    assert contenido.startswith(b"%PDF")
    assert textos_del_pie["derecha"] == ["Página 1 de 1"]


def test_encabezado_con_nombre_y_datos_del_despacho(despacho):
    tabla, linea = pdf.encabezado_documento(despacho, 500, "Cuenta de cobro", lineas=["N.º 12", ""])
    assert isinstance(tabla, Table)
    assert isinstance(linea, HRFlowable)
    izquierda, derecha = tabla._cellvalues[0]
    assert [p.text for p in izquierda] == [
        "Despacho de Prueba",
        "NIT 900123456 · Calle 1 # 2-3 · Bogotá D.C.<br/>3001234567 · despacho@ejemplo.co",
    ]
    # Las líneas vacías no se pintan.
    assert [p.text for p in derecha] == ["Cuenta de cobro", "N.º 12"]


def test_los_datos_del_encabezado_van_en_dos_renglones_y_escapados(despacho):
    despacho.direccion = "<Calle> & 5"
    despacho.telefono = ""
    despacho.correo = ""
    assert pdf._lineas_despacho(despacho) == ["NIT 900123456 · &lt;Calle&gt; &amp; 5 · Bogotá D.C."]
    assert pdf._lineas_despacho(None) == []


def test_encabezado_escapa_el_nombre_del_despacho(despacho):
    despacho.nombre_despacho = "<b>Despacho</b>"
    tabla, _ = pdf.encabezado_documento(despacho, 500, "Título")
    assert "<b>" not in tabla._cellvalues[0][0][0].text


def test_estilo_tabla_cebra_resaltadas_y_totales():
    comandos = pdf.estilo_tabla(resaltadas=[0], filas_total=1, total_filas=6).getCommands()
    fondos = {c[1]: c[3] for c in comandos if c[0] == "BACKGROUND"}
    # Encabezado teal, fila 1 (primera de datos) en rojo y cebra en las pares sin tocar el total.
    assert fondos[(0, 0)] == pdf.color(paleta.TEAL)
    assert fondos[(0, 1)] == pdf.color(paleta.TINTE_ROJO)
    assert (0, 2) in fondos and (0, 4) in fondos
    assert (0, 6) not in fondos
    assert ("FONTNAME", (0, -1), (-1, -1), pdf.letras()["texto_negrita"]) in comandos
    # Doble línea bajo el último total.
    # (operación, inicio, fin, grosor, color, tapa, guion, unión, cantidad de líneas, espacio)
    assert any(c[0] == "LINEBELOW" and c[1] == (0, -1) and len(c) > 8 and c[8] == 2 for c in comandos)


def test_estilo_tabla_sin_cebra():
    comandos = pdf.estilo_tabla(cebra=False, total_filas=6).getCommands()
    assert [c for c in comandos if c[0] == "BACKGROUND"] == [
        ("BACKGROUND", (0, 0), (-1, 0), pdf.color(paleta.TEAL))
    ]


def test_cuadro_datos_completa_la_ultima_fila():
    tabla = pdf.cuadro_datos([("Cliente", "A"), ("NIT", "1"), ("Fecha", "hoy")], 600, columnas=2)
    assert len(tabla._cellvalues) == 2
    assert tabla._cellvalues[1][1] == ""
    assert tabla._cellvalues[0][0][0].text == "CLIENTE"


def test_ancho_util_descuenta_margenes_y_relleno():
    assert pdf.ancho_util(A4) == pytest.approx(A4[0] - 2 * 2.2 * pdf.cm - 12)
    assert pdf.ancho_util(landscape(A4), margen_lateral=pdf.cm) == pytest.approx(
        landscape(A4)[0] - 2 * pdf.cm - 12
    )


# ---------------------------------------------------------------------------
# Letras de la marca
# ---------------------------------------------------------------------------


def test_usa_las_letras_de_la_plataforma():
    from reportlab.pdfbase import pdfmetrics

    assert pdf.letras() == pdf.LETRAS_DE_MARCA
    assert {"OpenSans", "OpenSans-Bold", "Montserrat-Bold"} <= set(pdfmetrics.getRegisteredFontNames())
    assert pdf.estilos_documento()["normal"].fontName == "OpenSans"
    assert pdf.estilos_documento()["titulo"].fontName == "Montserrat-Bold"


def test_si_faltan_los_archivos_de_letra_no_falla(tmp_path):
    assert pdf.registrar_fuentes(tmp_path) is False


def test_sin_letras_de_marca_el_pdf_sale_con_helvetica(monkeypatch, despacho):
    pdf.letras.cache_clear()
    monkeypatch.setattr(pdf, "RUTA_FUENTES", "/ruta/que/no/existe")
    monkeypatch.setattr(pdf, "registrar_fuentes", lambda ruta=None: False)
    try:
        assert pdf.letras() == pdf.LETRAS_DE_RESPALDO
        estilos = pdf.estilos_documento()
        contenido = pdf.construir_pdf(
            [Paragraph("Texto <b>en negrilla</b>", estilos["normal"])],
            tamano=A4,
            titulo="Prueba",
            despacho=despacho,
        )
        assert contenido.startswith(b"%PDF")
    finally:
        pdf.letras.cache_clear()


# ---------------------------------------------------------------------------
# Encabezado con logo, etiqueta y piezas comunes
# ---------------------------------------------------------------------------


def _logo(tmp_path, ancho=400, alto=400):
    from PIL import Image as PILImage

    ruta = tmp_path / "logo.png"
    PILImage.new("RGB", (ancho, alto), color="teal").save(ruta)
    return SimpleNamespace(path=str(ruta))


def test_con_logo_el_nombre_del_despacho_sigue_visible(despacho, tmp_path):
    """El logo no reemplaza al nombre: van juntos, el logo a la izquierda."""
    from reportlab.platypus import Image

    despacho.membrete = _logo(tmp_path)
    tabla, _ = pdf.encabezado_documento(despacho, 500, "No. 7", etiqueta="CUENTA DE COBRO")
    izquierda, derecha = tabla._cellvalues[0]
    (bloque,) = izquierda
    logo, textos = bloque._cellvalues[0]
    assert isinstance(logo, Image)
    assert logo.drawHeight == pytest.approx(pdf.ALTO_LOGO)
    assert textos[0].text == "Despacho de Prueba"
    assert "despacho@ejemplo.co" in textos[1].text
    assert [p.text for p in derecha] == ["CUENTA DE COBRO", "No. 7"]


def test_un_logo_ancho_no_pasa_del_ancho_maximo(despacho, tmp_path):
    despacho.membrete = _logo(tmp_path, ancho=1200, alto=200)
    tabla, _ = pdf.encabezado_documento(despacho, 500, "Título")
    logo = tabla._cellvalues[0][0][0]._cellvalues[0][0]
    assert logo.drawWidth == pytest.approx(pdf.ANCHO_LOGO)
    assert logo.drawHeight < pdf.ALTO_LOGO


def test_tarjetas_resumen_escapan_y_separan_las_cifras():
    tabla = pdf.tarjetas_resumen([("Clientes", 12), ("<b>Total</b>", "$ 1.000")], 500)
    fila = tabla._cellvalues[0]
    assert len(fila) == 3  # Dos tarjetas y el espacio entre ellas.
    assert fila[1] == ""
    assert fila[0][0].text == "CLIENTES"
    assert "<b>" not in fila[2][0].text


def test_subtitulo_de_seccion_lleva_barra_y_detalle():
    tabla, espacio = pdf.subtitulo_seccion("Cartera", 500, detalle="3 registros")
    assert "Cartera" in tabla._cellvalues[0][0].text and "3 registros" in tabla._cellvalues[0][0].text
    assert any(c[0] == "LINEBEFORE" for c in tabla._linecmds)
    assert espacio.height > 0


def test_cuadro_destacado_reparte_el_ancho():
    tabla = pdf.cuadro_destacado(["izquierda"], ["derecha"], 500, proporcion=0.6)
    assert tabla._colWidths == [pytest.approx(300), pytest.approx(200)]


# ---------------------------------------------------------------------------
# Sello en diagonal
# ---------------------------------------------------------------------------


@pytest.fixture
def sellos(monkeypatch):
    estampados = []
    monkeypatch.setattr(
        pdf._LienzoConPie, "drawCentredString", lambda lienzo, x, y, texto, *a, **k: estampados.append(texto)
    )
    return estampados


def test_el_sello_se_estampa_en_cada_hoja(despacho, sellos):
    estilos = pdf.estilos_documento()
    elementos = [Paragraph("Uno", estilos["normal"]), PageBreak(), Paragraph("Dos", estilos["normal"])]
    pdf.construir_pdf(elementos, tamano=A4, titulo="Prueba", despacho=despacho, sello="PAGADA")
    assert sellos == ["PAGADA", "PAGADA"]


def test_sin_sello_no_se_estampa_nada(despacho, sellos):
    estilos = pdf.estilos_documento()
    pdf.construir_pdf([Paragraph("Uno", estilos["normal"])], tamano=A4, titulo="Prueba", despacho=despacho)
    assert sellos == []
