"""
Utilidades de PDF compartidas por los módulos que generan documentos con
ReportLab (Módulo 4: documentos y certificados; Módulo 6: cuentas de cobro;
Módulo 10: reportes).
"""

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph


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
