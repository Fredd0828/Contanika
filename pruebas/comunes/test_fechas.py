"""Pruebas de las fechas en español correcto (mes en minúscula)."""

import datetime

from aplicaciones.comunes.fechas import fecha_larga

FECHA = datetime.date(2026, 11, 16)


def test_fecha_larga_con_el_mes_en_minuscula():
    assert fecha_larga(FECHA) == "16 de noviembre de 2026"


def test_fecha_larga_respeta_otros_formatos():
    assert fecha_larga(FECHA, "F Y") == "noviembre 2026"
    assert fecha_larga(FECHA, "SHORT_DATE_FORMAT") == "16/11/2026"


def test_fecha_larga_en_todos_los_meses():
    for mes in range(1, 13):
        texto = fecha_larga(datetime.date(2026, mes, 1))
        assert texto == texto.lower()
