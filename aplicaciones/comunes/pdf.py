"""
Utilidades de PDF compartidas por los módulos que generan documentos con
ReportLab (Módulo 4: documentos y certificados; Módulo 6: cuentas de cobro;
Módulo 10: reportes).
"""

import io

from django.utils.html import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import paleta

# Medidas comunes de la hoja: la franja de color de arriba y el pie con el
# despacho y el número de página.
ALTO_FRANJA = 0.28 * cm
ALTURA_PIE = 1.0 * cm
MARGEN_SUPERIOR = 1.7 * cm
MARGEN_INFERIOR = 1.9 * cm


def imagen_proporcional(ruta, ancho_maximo, alto_maximo, alineacion="CENTER"):
    """
    Imagen escalada sin deformarla para caber en el espacio indicado.

    `alineacion` es la posición horizontal en la página ("LEFT", "CENTER" o
    "RIGHT"); ReportLab centra las imágenes si no se indica otra cosa.
    """
    ancho_original, alto_original = ImageReader(ruta).getSize()
    escala = min(ancho_maximo / ancho_original, alto_maximo / alto_original)
    imagen = Image(ruta, width=ancho_original * escala, height=alto_original * escala)
    imagen.hAlign = alineacion
    return imagen


def encabezado_despacho(despacho, estilos, ancho_maximo, alto_maximo=3 * cm):
    """
    Elementos del encabezado del PDF: la imagen del membrete del despacho si
    el Administrador la cargó (escalada sin deformarla para caber en el ancho
    útil de la página), o el nombre y la ciudad del despacho como texto.

    Sin membrete, el nombre y la ciudad forman un solo bloque centrado: la
    ciudad va debajo del nombre con la misma alineación.
    """
    if despacho and despacho.membrete:
        return [imagen_proporcional(despacho.membrete.path, ancho_maximo, alto_maximo)]

    elementos = [Paragraph(despacho.nombre_despacho if despacho else "", estilos["Title"])]
    if despacho and despacho.ciudad:
        estilo_ciudad = ParagraphStyle("CiudadDespacho", parent=estilos["Normal"], alignment=TA_CENTER)
        elementos.append(Paragraph(despacho.ciudad, estilo_ciudad))
    return elementos


# ---------------------------------------------------------------------------
# Presentación común de los PDF
# ---------------------------------------------------------------------------
#
# Todos los PDF de la plataforma (reportes, cuentas de cobro, documentos y
# certificados) se arman con las mismas piezas, para que se vean como una sola
# papelería: franja de color arriba, encabezado con el despacho a la izquierda
# y el título del documento a la derecha, tablas con el mismo estilo y un pie
# con los datos del despacho y «Página X de Y».


def color(hexadecimal):
    """Color de la paleta en el formato de ReportLab."""
    return colors.HexColor(hexadecimal)


def estilos_documento():
    """Estilos de texto comunes: una sola familia y una escala corta de tamaños."""
    base = ParagraphStyle(
        "base", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=color(paleta.NAVY)
    )
    apagado = color(paleta.TEXTO_APAGADO)
    return {
        "normal": base,
        "derecha": ParagraphStyle("derecha", parent=base, alignment=TA_RIGHT),
        "cuerpo": ParagraphStyle("cuerpo", parent=base, fontSize=11, leading=17.5, alignment=TA_JUSTIFY),
        "despacho": ParagraphStyle(
            "despacho", parent=base, fontName="Helvetica-Bold", fontSize=14, leading=17
        ),
        "despacho_datos": ParagraphStyle(
            "despacho_datos", parent=base, fontSize=8, leading=11, textColor=color(paleta.TEXTO_TENUE)
        ),
        "titulo": ParagraphStyle(
            "titulo",
            parent=base,
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            alignment=TA_RIGHT,
            textColor=color(paleta.TEAL_OSCURO),
        ),
        "titulo_datos": ParagraphStyle(
            "titulo_datos", parent=base, fontSize=8.5, leading=12, alignment=TA_RIGHT, textColor=apagado
        ),
        "titulo_centrado": ParagraphStyle(
            "titulo_centrado",
            parent=base,
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=20,
            alignment=TA_CENTER,
        ),
        "subtitulo": ParagraphStyle(
            "subtitulo",
            parent=base,
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            spaceBefore=4,
            spaceAfter=5,
            textColor=color(paleta.TEAL_OSCURO),
        ),
        "etiqueta": ParagraphStyle(
            "etiqueta", parent=base, fontName="Helvetica-Bold", fontSize=7, leading=9.5, textColor=apagado
        ),
        "valor": ParagraphStyle("valor", parent=base, fontName="Helvetica-Bold", fontSize=10.5, leading=14),
        "cifra": ParagraphStyle("cifra", parent=base, fontName="Helvetica-Bold", fontSize=13, leading=16),
        "nota": ParagraphStyle(
            "nota", parent=base, fontSize=8, leading=11, textColor=color(paleta.TEXTO_TENUE)
        ),
        "nota_roja": ParagraphStyle(
            "nota_roja", parent=base, fontSize=8, leading=11, textColor=color(paleta.MARRON)
        ),
        "celda": ParagraphStyle("celda", parent=base, fontSize=7.5, leading=9.5),
        "celda_derecha": ParagraphStyle(
            "celda_derecha", parent=base, fontSize=7.5, leading=9.5, alignment=TA_RIGHT
        ),
        "celda_titulo": ParagraphStyle(
            "celda_titulo",
            parent=base,
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.white,
        ),
        "celda_titulo_derecha": ParagraphStyle(
            "celda_titulo_derecha",
            parent=base,
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.white,
            alignment=TA_RIGHT,
        ),
    }


def _datos_despacho(despacho, separador=" · "):
    """NIT, dirección, ciudad, teléfono y correo del despacho (los que estén cargados)."""
    if not despacho:
        return ""
    partes = [
        f"NIT {despacho.nit_despacho}" if despacho.nit_despacho else "",
        despacho.direccion,
        despacho.ciudad,
        despacho.telefono,
        despacho.correo,
    ]
    return separador.join(parte for parte in partes if parte)


def encabezado_documento(despacho, ancho, titulo, lineas=(), estilos=None):
    """
    Encabezado común: a la izquierda el despacho (su membrete, si lo cargó, o
    su nombre con los datos de contacto) y a la derecha el título del
    documento con sus datos (número, fecha, quién lo generó). Cierra con una
    línea teal que lo separa del contenido.

    `titulo` y `lineas` ya deben venir escapados si traen texto de un usuario.
    """
    estilos = estilos or estilos_documento()
    ancho_izquierdo = ancho * 0.52
    if despacho and despacho.membrete:
        izquierda = [
            imagen_proporcional(despacho.membrete.path, ancho_izquierdo, 2.2 * cm, alineacion="LEFT")
        ]
    else:
        izquierda = [Paragraph(escape(despacho.nombre_despacho) if despacho else "", estilos["despacho"])]
        datos = _datos_despacho(despacho)
        if datos:
            izquierda.append(Paragraph(escape(datos), estilos["despacho_datos"]))
    derecha = [Paragraph(titulo, estilos["titulo"])]
    derecha += [Paragraph(linea, estilos["titulo_datos"]) for linea in lineas if linea]
    tabla = Table([[izquierda, derecha]], colWidths=[ancho_izquierdo, ancho - ancho_izquierdo])
    tabla.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    linea = HRFlowable(width="100%", thickness=1.4, color=color(paleta.TEAL), spaceBefore=9, spaceAfter=12)
    return [tabla, linea]


def estilo_tabla(resaltadas=(), filas_total=0, cebra=True, total_filas=None):
    """
    Estilo común de las tablas: encabezado teal con texto blanco, renglones
    separados por una línea fina (sin rejilla vertical), fondo alterno suave
    y, si se pide, las últimas `filas_total` filas como totales en negrilla.
    `resaltadas` son los índices de fila de datos (desde 0) que van en rojo.
    """
    borde = color(paleta.BORDE_SUAVE)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), color(paleta.TEAL)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), color(paleta.NAVY)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, borde),
        ("BOX", (0, 0), (-1, -1), 0.6, color(paleta.BORDE)),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]
    if cebra and total_filas:
        ultima = total_filas - filas_total
        for fila in range(2, ultima + 1, 2):
            estilo.append(("BACKGROUND", (0, fila), (-1, fila), color(paleta.SUPERFICIE)))
    for indice in resaltadas:
        estilo.append(("BACKGROUND", (0, indice + 1), (-1, indice + 1), color(paleta.TINTE_ROJO)))
    if filas_total:
        estilo += [
            ("FONTNAME", (0, -filas_total), (-1, -1), "Helvetica-Bold"),
            ("LINEABOVE", (0, -filas_total), (-1, -filas_total), 0.8, color(paleta.TEAL)),
        ]
    return TableStyle(estilo)


def cuadro_datos(pares, ancho, columnas, estilos=None):
    """
    Cuadro de datos del documento: cada dato lleva su etiqueta pequeña en
    mayúsculas y el valor debajo, repartidos en `columnas` columnas iguales
    sobre un fondo suave. `pares` es una lista de (etiqueta, valor escapado).
    """
    estilos = estilos or estilos_documento()
    celdas = [
        [Paragraph(escape(etiqueta).upper(), estilos["etiqueta"]), Paragraph(valor, estilos["valor"])]
        for etiqueta, valor in pares
    ]
    filas = [celdas[i : i + columnas] for i in range(0, len(celdas), columnas)]
    filas[-1] += [""] * (columnas - len(filas[-1]))
    tabla = Table(filas, colWidths=[ancho / columnas] * columnas)
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color(paleta.SUPERFICIE)),
                ("BOX", (0, 0), (-1, -1), 0.6, color(paleta.BORDE)),
                ("LINEAFTER", (0, 0), (-2, -1), 0.4, color(paleta.BORDE_SUAVE)),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, color(paleta.BORDE_SUAVE)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return tabla


class _LienzoConPie(canvas.Canvas):
    """
    Lienzo que, al terminar, pinta en cada página la franja de color de arriba
    y el pie con los datos del despacho y «Página X de Y». El total de páginas
    solo se conoce al final, por eso las páginas se guardan y se cierran juntas.
    """

    texto_pie = ""
    margen_pie = 1.5 * cm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._paginas = []

    def showPage(self):
        self._paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._paginas)
        for estado in self._paginas:
            self.__dict__.update(estado)
            self._decorar(total)
            super().showPage()
        super().save()

    def _decorar(self, total):
        ancho, alto = self._pagesize
        margen = self.margen_pie
        self.saveState()
        # Franja superior en el degradado de la marca (navy a teal).
        trazo = self.beginPath()
        trazo.rect(0, alto - ALTO_FRANJA, ancho, ALTO_FRANJA)
        self.clipPath(trazo, stroke=0, fill=0)
        self.linearGradient(
            0,
            alto,
            ancho,
            alto,
            (color(paleta.NAVY), color(paleta.TEAL_OSCURO), color(paleta.TEAL)),
            extend=True,
        )
        self.restoreState()

        self.saveState()
        self.setStrokeColor(color(paleta.BORDE))
        self.setLineWidth(0.6)
        self.line(margen, ALTURA_PIE + 0.35 * cm, ancho - margen, ALTURA_PIE + 0.35 * cm)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(color(paleta.TEXTO_APAGADO))
        numero = f"Página {self._pageNumber} de {total}"
        self.drawRightString(ancho - margen, ALTURA_PIE, numero)
        # El texto del despacho se recorta si no cabe junto al número de página.
        disponible = ancho - 2 * margen - stringWidth(numero, "Helvetica", 7.5) - 0.6 * cm
        texto = self.texto_pie
        while texto and stringWidth(texto, "Helvetica", 7.5) > disponible:
            texto = texto[:-2].rstrip() + "…"
        self.drawString(margen, ALTURA_PIE, texto)
        self.restoreState()


def construir_pdf(elementos, *, tamano, titulo, despacho, margen_lateral=2.2 * cm):
    """
    Arma el PDF con la hoja común (franja superior, márgenes y pie paginado) y
    devuelve sus bytes. `elementos` es la lista de piezas de Platypus.
    """
    salida = io.BytesIO()
    documento = SimpleDocTemplate(
        salida,
        pagesize=tamano,
        leftMargin=margen_lateral,
        rightMargin=margen_lateral,
        topMargin=MARGEN_SUPERIOR,
        bottomMargin=MARGEN_INFERIOR,
        title=titulo,
        author=despacho.nombre_despacho if despacho else "",
    )
    nombre = despacho.nombre_despacho if despacho else ""
    datos = _datos_despacho(despacho)
    pie = type(
        "LienzoDelDocumento",
        (_LienzoConPie,),
        # El pie se alinea con el contenido (el marco deja 6 puntos de relleno).
        {"texto_pie": " · ".join(p for p in (nombre, datos) if p), "margen_pie": margen_lateral + 6},
    )
    documento.build(elementos, canvasmaker=pie)
    return salida.getvalue()


def ancho_util(tamano, margen_lateral=2.2 * cm):
    """Ancho disponible para el contenido en una hoja del tamaño indicado."""
    # El marco de la página deja 6 puntos de relleno a cada lado.
    return tamano[0] - 2 * margen_lateral - 12


def separador(alto_cm):
    """Espacio vertical entre bloques."""
    return Spacer(1, alto_cm * cm)
