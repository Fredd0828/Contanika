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
    assert [p.text for p in izquierda] == ["Despacho de Prueba", pdf._datos_despacho(despacho)]
    # Las líneas vacías no se pintan.
    assert [p.text for p in derecha] == ["Cuenta de cobro", "N.º 12"]


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
    assert ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold") in comandos


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
