"""
Fechas escritas en español correcto.

La traducción de Django escribe los meses con mayúscula («16 de Noviembre de
2026»), pero en español los meses van en minúscula. `fecha_larga` usa el
formato de Django y baja a minúscula solo el nombre del mes.
"""

from django.utils.formats import date_format


def fecha_larga(fecha, formato=None):
    """
    Devuelve la fecha con el formato indicado (por defecto «16 de noviembre de
    2026») y el nombre del mes en minúscula. Acepta los mismos formatos que
    `date_format` de Django.
    """
    texto = date_format(fecha, formato)
    mes = date_format(fecha, "F")
    return texto.replace(mes, mes.lower())
