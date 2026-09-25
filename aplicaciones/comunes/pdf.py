"""
Utilidades de PDF compartidas por los módulos que generan documentos con
ReportLab (Módulo 4: documentos y certificados; Módulo 6: cuentas de cobro).
"""

from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph


def encabezado_despacho(despacho, estilos, ancho_maximo, alto_maximo=3 * cm):
    """
    Elementos del encabezado del PDF: la imagen del membrete del despacho si
    el Administrador la cargó (escalada sin deformarla para caber en el ancho
    útil de la página), o el nombre y la ciudad del despacho como texto.
    """
    if despacho and despacho.membrete:
        ancho_original, alto_original = ImageReader(despacho.membrete.path).getSize()
        escala = min(ancho_maximo / ancho_original, alto_maximo / alto_original)
        return [Image(despacho.membrete.path, width=ancho_original * escala, height=alto_original * escala)]

    elementos = [Paragraph(despacho.nombre_despacho if despacho else "", estilos["Title"])]
    if despacho and despacho.ciudad:
        elementos.append(Paragraph(despacho.ciudad, estilos["Normal"]))
    return elementos
