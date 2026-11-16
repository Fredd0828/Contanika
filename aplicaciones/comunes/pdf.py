"""
Utilidades de PDF compartidas por los módulos que generan documentos con
ReportLab (Módulo 4: documentos y certificados; Módulo 6: cuentas de cobro;
Módulo 10: reportes).

Todos los PDF de la plataforma se arman con las mismas piezas, para que se
vean como una sola papelería: franja de color arriba, encabezado con el logo
y los datos del despacho a la izquierda y el tipo y número del documento a la
derecha, tablas con el mismo estilo y un pie con los datos del despacho y
«Página X de Y». Las letras son las de la plataforma: Montserrat en títulos
y Open Sans en el texto (`fuentes/`, licencia OFL); si faltaran los archivos,
se usa Helvetica y el PDF sale igual.
"""

import io
from functools import lru_cache
from pathlib import Path

from django.utils.html import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFError, TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import paleta

# Medidas comunes de la hoja: la franja de color de arriba y el pie con el
# despacho y el número de página.
ALTO_FRANJA = 0.28 * cm
ALTURA_PIE = 1.0 * cm
MARGEN_SUPERIOR = 1.7 * cm
MARGEN_INFERIOR = 1.9 * cm
ALTO_LOGO = 1.7 * cm
ANCHO_LOGO = 3.4 * cm

# ---------------------------------------------------------------------------
# Letras
# ---------------------------------------------------------------------------

RUTA_FUENTES = Path(__file__).resolve().parent / "fuentes"
ARCHIVOS_FUENTES = {
    "Montserrat": "Montserrat-Regular.ttf",
    "Montserrat-SemiBold": "Montserrat-SemiBold.ttf",
    "Montserrat-Bold": "Montserrat-Bold.ttf",
    "OpenSans": "OpenSans-Regular.ttf",
    "OpenSans-Italic": "OpenSans-Italic.ttf",
    "OpenSans-SemiBold": "OpenSans-SemiBold.ttf",
    "OpenSans-Bold": "OpenSans-Bold.ttf",
}
LETRAS_DE_MARCA = {
    "texto": "OpenSans",
    "texto_semi": "OpenSans-SemiBold",
    "texto_negrita": "OpenSans-Bold",
    "cursiva": "OpenSans-Italic",
    "titulo": "Montserrat-Bold",
    "titulo_semi": "Montserrat-SemiBold",
}
LETRAS_DE_RESPALDO = {
    "texto": "Helvetica",
    "texto_semi": "Helvetica-Bold",
    "texto_negrita": "Helvetica-Bold",
    "cursiva": "Helvetica-Oblique",
    "titulo": "Helvetica-Bold",
    "titulo_semi": "Helvetica-Bold",
}


def registrar_fuentes(ruta=RUTA_FUENTES):
    """
    Registra Montserrat y Open Sans en ReportLab. Devuelve False (y no
    registra nada a medias) si falta o está dañado algún archivo.
    """
    try:
        fuentes = [TTFont(nombre, str(Path(ruta) / archivo)) for nombre, archivo in ARCHIVOS_FUENTES.items()]
    except (OSError, TTFError):
        return False
    for fuente in fuentes:
        pdfmetrics.registerFont(fuente)
    # Así <b> e <i> dentro de un párrafo usan la variante correcta de la letra.
    pdfmetrics.registerFontFamily(
        "OpenSans",
        normal="OpenSans",
        bold="OpenSans-Bold",
        italic="OpenSans-Italic",
        boldItalic="OpenSans-Bold",
    )
    pdfmetrics.registerFontFamily(
        "Montserrat",
        normal="Montserrat",
        bold="Montserrat-Bold",
        italic="Montserrat",
        boldItalic="Montserrat-Bold",
    )
    return True


@lru_cache(maxsize=1)
def letras():
    """Nombres de letra a usar: las de la marca si están disponibles; si no, Helvetica."""
    return dict(LETRAS_DE_MARCA if registrar_fuentes() else LETRAS_DE_RESPALDO)


# ---------------------------------------------------------------------------
# Piezas básicas
# ---------------------------------------------------------------------------


def color(hexadecimal):
    """Color de la paleta en el formato de ReportLab."""
    return colors.HexColor(hexadecimal)


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


def estilos_documento():
    """Estilos de texto comunes: dos familias (títulos y texto) y una escala corta de tamaños."""
    letra = letras()
    navy = color(paleta.NAVY)
    apagado = color(paleta.TEXTO_APAGADO)
    tenue = color(paleta.TEXTO_TENUE)
    base = ParagraphStyle("base", fontName=letra["texto"], fontSize=9.5, leading=14, textColor=navy)

    def estilo(nombre, **cambios):
        return ParagraphStyle(nombre, parent=base, **cambios)

    return {
        "normal": base,
        "derecha": estilo("derecha", alignment=TA_RIGHT),
        "cuerpo": estilo("cuerpo", fontSize=11, leading=18, alignment=TA_JUSTIFY),
        "despacho": estilo("despacho", fontName=letra["titulo"], fontSize=13, leading=16),
        "despacho_datos": estilo("despacho_datos", fontSize=7.5, leading=10.5, textColor=tenue),
        "titulo_etiqueta": estilo(
            "titulo_etiqueta",
            fontName=letra["titulo_semi"],
            fontSize=8,
            leading=10,
            alignment=TA_RIGHT,
            textColor=color(paleta.TEAL),
        ),
        "titulo": estilo("titulo", fontName=letra["titulo"], fontSize=17, leading=21, alignment=TA_RIGHT),
        "titulo_datos": estilo(
            "titulo_datos", fontSize=8, leading=11.5, alignment=TA_RIGHT, textColor=apagado
        ),
        "titulo_centrado": estilo(
            "titulo_centrado", fontName=letra["titulo"], fontSize=14, leading=19, alignment=TA_CENTER
        ),
        "subtitulo": estilo(
            "subtitulo",
            fontName=letra["titulo"],
            fontSize=10.5,
            leading=13,
            textColor=color(paleta.TEAL_OSCURO),
        ),
        "etiqueta": estilo(
            "etiqueta", fontName=letra["titulo_semi"], fontSize=6.8, leading=9, textColor=apagado
        ),
        "valor": estilo("valor", fontName=letra["texto_negrita"], fontSize=10, leading=13.5),
        "cifra": estilo("cifra", fontName=letra["titulo"], fontSize=14, leading=17),
        "nota": estilo("nota", fontSize=8, leading=11, textColor=tenue),
        "nota_roja": estilo("nota_roja", fontSize=8, leading=11, textColor=color(paleta.MARRON)),
        "celda": estilo("celda", fontSize=7.8, leading=10),
        "celda_derecha": estilo("celda_derecha", fontSize=7.8, leading=10, alignment=TA_RIGHT),
        "celda_titulo": estilo(
            "celda_titulo", fontName=letra["texto_semi"], fontSize=7.3, leading=9.5, textColor=colors.white
        ),
        "celda_titulo_derecha": estilo(
            "celda_titulo_derecha",
            fontName=letra["texto_semi"],
            fontSize=7.3,
            leading=9.5,
            textColor=colors.white,
            alignment=TA_RIGHT,
        ),
    }


def _sin_relleno(*comandos):
    """Estilo de una tabla de maquetación: sin bordes ni relleno."""
    return TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            *comandos,
        ]
    )


# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------


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


def _lineas_despacho(despacho, separador=" · "):
    """
    Datos del despacho para el encabezado, en dos renglones para que no se
    corten en un punto cualquiera: identificación y ubicación arriba,
    teléfono y correo abajo. Ya vienen escapados.
    """
    if not despacho:
        return []
    ubicacion = [
        f"NIT {despacho.nit_despacho}" if despacho.nit_despacho else "",
        despacho.direccion,
        despacho.ciudad,
    ]
    contacto = [despacho.telefono, despacho.correo]
    renglones = (separador.join(escape(p) for p in grupo if p) for grupo in (ubicacion, contacto))
    return [renglon for renglon in renglones if renglon]


def _bloque_despacho(despacho, ancho, estilos):
    """
    Logo del despacho (si lo cargó) y, siempre a su lado, el nombre con los
    datos de contacto. Sin logo, solo el nombre y los datos.
    """
    textos = [Paragraph(escape(despacho.nombre_despacho) if despacho else "", estilos["despacho"])]
    lineas = _lineas_despacho(despacho)
    if lineas:
        textos.append(Paragraph("<br/>".join(lineas), estilos["despacho_datos"]))
    if not (despacho and despacho.membrete):
        return textos
    logo = imagen_proporcional(despacho.membrete.path, ANCHO_LOGO, ALTO_LOGO, alineacion="LEFT")
    espacio = 0.35 * cm
    tabla = Table([[logo, textos]], colWidths=[logo.drawWidth + espacio, ancho - logo.drawWidth - espacio])
    tabla.setStyle(_sin_relleno())
    return [tabla]


def encabezado_documento(despacho, ancho, titulo, lineas=(), estilos=None, etiqueta=""):
    """
    Encabezado común. A la izquierda, el despacho: su logo (si lo cargó)
    junto a su nombre y datos de contacto. A la derecha, el tipo de documento
    en letra pequeña (`etiqueta`, por ejemplo «CUENTA DE COBRO»), el título o
    número en grande y sus datos (fecha, quién lo generó). Cierra con una
    línea teal que lo separa del contenido.

    `titulo`, `lineas` y `etiqueta` ya deben venir escapados si traen texto
    de un usuario.
    """
    estilos = estilos or estilos_documento()
    ancho_izquierdo = ancho * 0.62
    izquierda = _bloque_despacho(despacho, ancho_izquierdo - 0.4 * cm, estilos)
    derecha = [Paragraph(etiqueta, estilos["titulo_etiqueta"])] if etiqueta else []
    derecha.append(Paragraph(titulo, estilos["titulo"]))
    derecha += [Paragraph(linea, estilos["titulo_datos"]) for linea in lineas if linea]
    tabla = Table([[izquierda, derecha]], colWidths=[ancho_izquierdo, ancho - ancho_izquierdo])
    tabla.setStyle(_sin_relleno())
    linea = HRFlowable(width="100%", thickness=1.2, color=color(paleta.TEAL), spaceBefore=10, spaceAfter=14)
    return [tabla, linea]


# ---------------------------------------------------------------------------
# Tablas, cuadros y secciones
# ---------------------------------------------------------------------------


def estilo_tabla(resaltadas=(), filas_total=0, cebra=True, total_filas=None):
    """
    Estilo común de las tablas: encabezado teal con texto blanco, renglones
    separados por una línea fina (sin rejilla vertical), fondo alterno suave
    y, si se pide, las últimas `filas_total` filas como totales en negrilla,
    con una línea arriba y doble línea al cierre, como en un estado de cuenta.
    `resaltadas` son los índices de fila de datos (desde 0) que van en rojo.
    """
    letra = letras()
    borde = color(paleta.BORDE_SUAVE)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), color(paleta.TEAL)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), letra["texto_semi"]),
        ("FONTNAME", (0, 1), (-1, -1), letra["texto"]),
        ("FONTSIZE", (0, 0), (-1, -1), 8.8),
        ("TEXTCOLOR", (0, 1), (-1, -1), color(paleta.NAVY)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, borde),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, color(paleta.BORDE)),
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
        teal = color(paleta.TEAL)
        estilo += [
            ("FONTNAME", (0, -filas_total), (-1, -1), letra["texto_negrita"]),
            ("LINEABOVE", (0, -filas_total), (-1, -filas_total), 0.8, teal),
            # Doble línea bajo el último total (cuenta, ancho, color, tapa, guion, unión, veces, espacio).
            ("LINEBELOW", (0, -1), (-1, -1), 0.7, teal, None, None, None, 2, 1.4),
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
                ("BOX", (0, 0), (-1, -1), 0.5, color(paleta.BORDE)),
                ("LINEAFTER", (0, 0), (-2, -1), 0.4, color(paleta.BORDE_SUAVE)),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, color(paleta.BORDE_SUAVE)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 11),
                ("RIGHTPADDING", (0, 0), (-1, -1), 11),
            ]
        )
    )
    return tabla


def tarjetas_resumen(pares, ancho, estilos=None):
    """
    Cifras principales en una fila de tarjetas: etiqueta pequeña y valor
    grande, con una raya teal arriba. `pares` es una lista de (etiqueta, valor)
    en texto plano: aquí se escapan.
    """
    estilos = estilos or estilos_documento()
    celdas = [
        [
            Paragraph(escape(str(etiqueta)).upper(), estilos["etiqueta"]),
            Spacer(1, 3),
            Paragraph(escape(str(valor)), estilos["cifra"]),
        ]
        for etiqueta, valor in pares
    ]
    separacion = 0.3 * cm
    ancho_tarjeta = (ancho - separacion * (len(celdas) - 1)) / len(celdas)
    columnas, anchos = [], []
    for posicion, celda in enumerate(celdas):
        if posicion:
            columnas.append("")
            anchos.append(separacion)
        columnas.append(celda)
        anchos.append(ancho_tarjeta)
    tabla = Table([columnas], colWidths=anchos)
    estilo = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 11),
    ]
    for columna in range(0, len(columnas), 2):
        estilo += [
            ("BACKGROUND", (columna, 0), (columna, 0), color(paleta.SUPERFICIE)),
            ("BOX", (columna, 0), (columna, 0), 0.5, color(paleta.BORDE)),
            ("LINEABOVE", (columna, 0), (columna, 0), 2, color(paleta.TEAL)),
        ]
    tabla.setStyle(TableStyle(estilo))
    return tabla


def cuadro_destacado(izquierda, derecha, ancho, proporcion=0.58):
    """
    Recuadro para el dato central del documento (por ejemplo, quién debe y
    cuánto): dos columnas de piezas sobre fondo crema con raya teal arriba.
    """
    tabla = Table([[izquierda, derecha]], colWidths=[ancho * proporcion, ancho * (1 - proporcion)])
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color(paleta.CREMA_SUAVE)),
                ("BOX", (0, 0), (-1, -1), 0.5, color(paleta.BORDE)),
                ("LINEABOVE", (0, 0), (-1, 0), 2, color(paleta.TEAL)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ]
        )
    )
    return tabla


def subtitulo_seccion(texto, ancho, estilos=None, detalle=""):
    """
    Título de una sección con una barra teal a la izquierda. `texto` ya debe
    venir escapado; `detalle` es un dato pequeño al lado (por ejemplo, cuántos
    registros tiene), también escapado.
    """
    estilos = estilos or estilos_documento()
    if detalle:
        texto = (
            f'{texto} <font name="{letras()["texto"]}" size="8" color="{paleta.TEXTO_APAGADO}">'
            f"· {detalle}</font>"
        )
    tabla = Table([[Paragraph(texto, estilos["subtitulo"])]], colWidths=[ancho])
    tabla.setStyle(
        _sin_relleno(
            ("LINEBEFORE", (0, 0), (0, 0), 2.6, color(paleta.TEAL)),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        )
    )
    return [tabla, Spacer(1, 6)]


# ---------------------------------------------------------------------------
# Hoja: franja, pie paginado y sello
# ---------------------------------------------------------------------------


class _LienzoConPie(canvas.Canvas):
    """
    Lienzo que, al terminar, pinta en cada página la franja de color de arriba,
    el pie con los datos del despacho y «Página X de Y» y, si se pidió, un
    sello en diagonal (por ejemplo «PAGADA»). El total de páginas solo se
    conoce al final, por eso las páginas se guardan y se cierran juntas.
    """

    texto_pie = ""
    margen_pie = 1.5 * cm
    sello = ""

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
        letra = letras()
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

        if self.sello:
            self._dibujar_sello(ancho, alto, letra["titulo"])

        self.saveState()
        self.setStrokeColor(color(paleta.BORDE))
        self.setLineWidth(0.5)
        self.line(margen, ALTURA_PIE + 0.35 * cm, ancho - margen, ALTURA_PIE + 0.35 * cm)
        self.setFont(letra["texto"], 7.3)
        self.setFillColor(color(paleta.TEXTO_APAGADO))
        numero = f"Página {self._pageNumber} de {total}"
        self.drawRightString(ancho - margen, ALTURA_PIE, numero)
        # El texto del despacho se recorta si no cabe junto al número de página.
        disponible = ancho - 2 * margen - stringWidth(numero, letra["texto"], 7.3) - 0.6 * cm
        texto = self.texto_pie
        while texto and stringWidth(texto, letra["texto"], 7.3) > disponible:
            texto = texto[:-2].rstrip() + "…"
        self.drawString(margen, ALTURA_PIE, texto)
        self.restoreState()

    def _dibujar_sello(self, ancho, alto, letra):
        """Sello en diagonal, verde y casi transparente, en el centro de la hoja."""
        tamano = 64
        verde = color(paleta.VERDE)
        ancho_texto = stringWidth(self.sello, letra, tamano)
        self.saveState()
        self.translate(ancho / 2, alto / 2)
        self.rotate(28)
        self.setFillColor(verde, alpha=0.11)
        self.setStrokeColor(verde, alpha=0.22)
        self.setLineWidth(3)
        relleno = 0.45 * cm
        self.roundRect(
            -ancho_texto / 2 - relleno,
            -tamano * 0.42,
            ancho_texto + 2 * relleno,
            tamano * 1.08,
            8,
            stroke=1,
            fill=0,
        )
        self.setFont(letra, tamano)
        self.drawCentredString(0, -tamano * 0.22, self.sello)
        self.restoreState()


def construir_pdf(elementos, *, tamano, titulo, despacho, margen_lateral=2.2 * cm, sello=""):
    """
    Arma el PDF con la hoja común (franja superior, márgenes y pie paginado) y
    devuelve sus bytes. `elementos` es la lista de piezas de Platypus. `sello`
    es un texto que se estampa en diagonal en cada hoja (por ejemplo «PAGADA»).
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
        creator="Contanika",
    )
    nombre = despacho.nombre_despacho if despacho else ""
    datos = _datos_despacho(despacho)
    pie = type(
        "LienzoDelDocumento",
        (_LienzoConPie,),
        {
            "texto_pie": " · ".join(p for p in (nombre, datos) if p),
            # El pie se alinea con el contenido (el marco deja 6 puntos de relleno).
            "margen_pie": margen_lateral + 6,
            "sello": sello,
        },
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
