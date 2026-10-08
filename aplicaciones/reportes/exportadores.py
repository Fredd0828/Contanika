"""
Exportación de los reportes del módulo 10 a Excel (openpyxl) y PDF (ReportLab).

Ambos formatos parten del mismo `ResultadoReporte`: encabezado con el
despacho, el reporte, la fecha, quién lo generó y los filtros; el resumen;
cada sección como tabla (filas resaltadas en rojo) y el gráfico de barras
cuando el reporte lo tiene.
"""

from datetime import date
from decimal import Decimal
from io import BytesIO

from django.utils import timezone
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.graphics.charts.barcharts import HorizontalBarChart, VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from aplicaciones.comunes import paleta
from aplicaciones.comunes.pdf import encabezado_despacho
from aplicaciones.finanzas.templatetags.finanzas_tags import formato_pesos
from aplicaciones.seguridad.models import ConfiguracionDespacho

from .resultados import FECHA, NUMERO, PESOS, PORCENTAJE

# Colores de la paleta de la plataforma (ver `comunes/paleta.py`).
COLOR_ENCABEZADO = paleta.sin_numeral(paleta.TEAL)
COLOR_RESALTADO = "FDE2E1"
COLORES_SERIES = paleta.SERIES_GRAFICO


def formatear(valor, tipo):
    """Texto de una celda para la pantalla y el PDF."""
    if valor is None or valor == "":
        return "—" if tipo in (PESOS, NUMERO, PORCENTAJE, FECHA) else ""
    if tipo == PESOS:
        return formato_pesos(valor)
    if tipo == FECHA and isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    if tipo == PORCENTAJE:
        return f"{valor:+.1f} %".replace(".", ",")
    return str(valor)


def _encabezado(definicion, usuario, filtros_texto):
    despacho = ConfiguracionDespacho.objects.first()
    return {
        "despacho": despacho.nombre_despacho if despacho else "",
        "titulo": f"Reporte de {definicion.nombre.lower()}",
        "generado": timezone.localtime().strftime("%d/%m/%Y %H:%M"),
        "usuario": usuario.nombre,
        "filtros": filtros_texto or "Sin filtros",
        "objeto_despacho": despacho,
    }


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------


def _valor_excel(valor, tipo):
    if valor is None:
        return None
    if tipo == PESOS:
        return float(valor)
    if tipo == PORCENTAJE:
        return valor / 100
    if isinstance(valor, Decimal):
        return float(valor)
    return valor


def exportar_excel(definicion, resultado, usuario, filtros_texto):
    """Libro de Excel con una hoja por sección y, si aplica, el gráfico nativo de Excel."""
    datos = _encabezado(definicion, usuario, filtros_texto)
    libro = Workbook()
    negrita = Font(bold=True)
    blanco = Font(bold=True, color="FFFFFF")
    relleno_encabezado = PatternFill("solid", fgColor=COLOR_ENCABEZADO)
    relleno_resaltado = PatternFill("solid", fgColor=COLOR_RESALTADO)
    texto_rojo = Font(color="B42318")

    for numero, seccion in enumerate(resultado.secciones):
        hoja = libro.active if numero == 0 else libro.create_sheet()
        hoja.title = seccion.titulo[:31].replace("/", "-").replace(":", "")
        hoja.append([datos["despacho"]])
        hoja.append([datos["titulo"]])
        hoja["A1"].font = Font(bold=True, size=13)
        hoja["A2"].font = Font(bold=True, size=12)
        hoja.append([f"Generado el {datos['generado']} por {datos['usuario']}"])
        hoja.append([f"Filtros: {datos['filtros']}"])
        if numero == 0:
            for etiqueta, valor in resultado.resumen:
                hoja.append([etiqueta, valor])
                hoja.cell(row=hoja.max_row, column=1).font = negrita
        hoja.append([])
        hoja.append([seccion.titulo])
        hoja.cell(row=hoja.max_row, column=1).font = negrita
        hoja.append([columna.titulo for columna in seccion.columnas])
        fila_titulos = hoja.max_row
        for celda in hoja[fila_titulos]:
            celda.font = blanco
            celda.fill = relleno_encabezado
            celda.alignment = Alignment(wrap_text=True, vertical="center")
        for indice, fila in enumerate(seccion.filas):
            hoja.append([_valor_excel(v, c.tipo) for v, c in zip(fila, seccion.columnas, strict=True)])
            for posicion, columna in enumerate(seccion.columnas, start=1):
                celda = hoja.cell(row=hoja.max_row, column=posicion)
                if columna.tipo == PESOS:
                    celda.number_format = '"$" #,##0'
                elif columna.tipo == FECHA:
                    celda.number_format = "DD/MM/YYYY"
                elif columna.tipo == PORCENTAJE:
                    celda.number_format = "0.0%"
                if indice in seccion.resaltadas:
                    celda.fill = relleno_resaltado
                    celda.font = texto_rojo
        if seccion.nota_resaltado and seccion.resaltadas:
            hoja.append([seccion.nota_resaltado])
        for posicion, columna in enumerate(seccion.columnas, start=1):
            hoja.column_dimensions[get_column_letter(posicion)].width = columna.ancho + 2
        hoja.freeze_panes = hoja.cell(row=fila_titulos + 1, column=1)

        if numero == 0 and resultado.grafico and seccion.filas:
            _grafico_excel(libro, resultado.grafico)

    for nota in resultado.notas:
        libro.worksheets[0].append([nota])

    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()


def _grafico_excel(libro, grafico):
    """Hoja «Gráfico» con los datos y un gráfico de barras nativo de Excel."""
    hoja = libro.create_sheet("Gráfico")
    hoja.append(["Categoría"] + [nombre for nombre, _ in grafico.series])
    for posicion, etiqueta in enumerate(grafico.etiquetas):
        hoja.append([etiqueta] + [valores[posicion] for _, valores in grafico.series])
    barras = BarChart()
    barras.type = "bar" if grafico.horizontal else "col"
    barras.title = grafico.titulo
    barras.y_axis.title = "Pesos"
    barras.height, barras.width = 10, 22
    datos = Reference(
        hoja, min_col=2, max_col=1 + len(grafico.series), min_row=1, max_row=1 + len(grafico.etiquetas)
    )
    categorias = Reference(hoja, min_col=1, min_row=2, max_row=1 + len(grafico.etiquetas))
    barras.add_data(datos, titles_from_data=True)
    barras.set_categories(categorias)
    # Sin esto Excel pinta las barras con el azul de su tema por defecto.
    for posicion, serie in enumerate(barras.series):
        color = paleta.sin_numeral(COLORES_SERIES[posicion % len(COLORES_SERIES)])
        serie.graphicalProperties.solidFill = color
        serie.graphicalProperties.line.solidFill = color
    hoja.add_chart(barras, f"{get_column_letter(len(grafico.series) + 3)}2")
    hoja.column_dimensions["A"].width = 30


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------


def _dibujo_grafico(grafico, ancho):
    """Gráfico de barras de ReportLab con su leyenda."""
    alto = 7.5 * cm if not grafico.horizontal else max(5 * cm, 0.75 * cm * len(grafico.etiquetas) + 2 * cm)
    dibujo = Drawing(ancho, alto)
    clase = HorizontalBarChart if grafico.horizontal else VerticalBarChart
    barras = clase()
    margen_izq = 5.5 * cm if grafico.horizontal else 2 * cm
    barras.x, barras.y = margen_izq, 1.2 * cm
    barras.width, barras.height = ancho - margen_izq - 4 * cm, alto - 2 * cm
    barras.data = [valores for _, valores in grafico.series]
    eje_categorias = barras.categoryAxis
    eje_categorias.categoryNames = grafico.etiquetas
    eje_categorias.labels.fontSize = 7
    if not grafico.horizontal:
        eje_categorias.labels.angle = 30
        eje_categorias.labels.dy = -6
    eje_valores = barras.valueAxis
    eje_valores.valueMin = 0
    eje_valores.labels.fontSize = 7
    eje_valores.labelTextFormat = lambda valor: formato_pesos(valor)
    for posicion, _ in enumerate(grafico.series):
        barras.bars[posicion].fillColor = colors.HexColor(COLORES_SERIES[posicion % len(COLORES_SERIES)])
    dibujo.add(barras)
    leyenda = Legend()
    leyenda.x, leyenda.y = ancho - 3.6 * cm, alto - 0.8 * cm
    leyenda.fontSize = 7
    leyenda.colorNamePairs = [
        (colors.HexColor(COLORES_SERIES[i % len(COLORES_SERIES)]), nombre)
        for i, (nombre, _) in enumerate(grafico.series)
    ]
    dibujo.add(leyenda)
    dibujo.add(String(0, alto - 0.4 * cm, grafico.titulo, fontSize=9, fontName="Helvetica-Bold"))
    return dibujo


def exportar_pdf(definicion, resultado, usuario, filtros_texto):
    """PDF horizontal con encabezado del despacho, resumen, gráfico y tablas."""
    datos = _encabezado(definicion, usuario, filtros_texto)
    salida = BytesIO()
    documento = SimpleDocTemplate(
        salida,
        pagesize=landscape(letter),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title=datos["titulo"],
    )
    estilos = getSampleStyleSheet()
    celda = ParagraphStyle("celda", parent=estilos["Normal"], fontSize=7, leading=8.5)
    celda_roja = ParagraphStyle("celda_roja", parent=celda, textColor=colors.HexColor("#B42318"))
    titulo_celda = ParagraphStyle(
        "titulo_celda", parent=celda, textColor=colors.white, fontName="Helvetica-Bold"
    )
    ancho_util = documento.width

    elementos = encabezado_despacho(datos["objeto_despacho"], estilos, ancho_util, alto_maximo=2.2 * cm)
    elementos += [
        Paragraph(datos["titulo"], estilos["Heading2"]),
        Paragraph(f"Generado el {datos['generado']} por {datos['usuario']}", estilos["Normal"]),
        Paragraph(f"Filtros: {datos['filtros']}", estilos["Normal"]),
        Spacer(1, 0.3 * cm),
    ]
    if resultado.resumen:
        tabla = Table([[Paragraph(f"<b>{e}</b><br/>{v}", celda) for e, v in resultado.resumen]])
        tabla.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F8F8")),
                ]
            )
        )
        elementos += [tabla, Spacer(1, 0.3 * cm)]
    if resultado.grafico and resultado.grafico.etiquetas:
        elementos += [_dibujo_grafico(resultado.grafico, ancho_util), Spacer(1, 0.3 * cm)]

    for seccion in resultado.secciones:
        elementos.append(Paragraph(seccion.titulo, estilos["Heading3"]))
        total_ancho = sum(columna.ancho for columna in seccion.columnas)
        anchos = [ancho_util * columna.ancho / total_ancho for columna in seccion.columnas]
        filas = [[Paragraph(columna.titulo, titulo_celda) for columna in seccion.columnas]]
        for indice, fila in enumerate(seccion.filas):
            estilo = celda_roja if indice in seccion.resaltadas else celda
            filas.append(
                [Paragraph(formatear(v, c.tipo), estilo) for v, c in zip(fila, seccion.columnas, strict=True)]
            )
        if not seccion.filas:
            filas.append(
                [Paragraph("Sin registros para los filtros elegidos.", celda)] + [""] * (len(anchos) - 1)
            )
        tabla = Table(filas, colWidths=anchos, repeatRows=1)
        estilo_tabla = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(f"#{COLOR_ENCABEZADO}")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CCCCCC")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
        for indice in seccion.resaltadas:
            estilo_tabla.append(
                ("BACKGROUND", (0, indice + 1), (-1, indice + 1), colors.HexColor(f"#{COLOR_RESALTADO}"))
            )
        tabla.setStyle(TableStyle(estilo_tabla))
        elementos.append(tabla)
        if seccion.nota_resaltado and seccion.resaltadas:
            elementos.append(Paragraph(seccion.nota_resaltado, celda_roja))
        elementos.append(Spacer(1, 0.3 * cm))
    for nota in resultado.notas:
        elementos.append(Paragraph(nota, celda))

    documento.build(elementos)
    return salida.getvalue()
