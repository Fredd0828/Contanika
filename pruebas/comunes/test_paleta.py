"""Pruebas de la paleta de colores: lo descargado debe verse como la plataforma."""

import re

import pytest
from django.conf import settings

from aplicaciones.comunes import paleta

HOJA_DE_ESTILOS = settings.RUTA_BASE / "estaticos" / "css" / "contanika.css"

# Azul primario de Bootstrap y sus variantes: no pertenecen a la paleta.
AZULES_DE_BOOTSTRAP = ["#0d6efd", "#0b5ed7", "#0a58ca", "#cfe2ff", "#86b7fe"]


@pytest.fixture(scope="module")
def estilos():
    return HOJA_DE_ESTILOS.read_text(encoding="utf-8").lower()


def _variable(estilos, nombre):
    return re.search(rf"--{nombre}:\s*(#[0-9a-f]{{6}})", estilos).group(1)


@pytest.mark.parametrize(
    ("constante", "variable"),
    [
        (paleta.NAVY, "navy"),
        (paleta.TEAL, "teal"),
        (paleta.NARANJA, "orange"),
        (paleta.VERDE, "green"),
        (paleta.ROJO, "red"),
        (paleta.CREMA, "cream"),
        (paleta.BORDE, "border2"),
    ],
)
def test_la_paleta_de_pdf_y_excel_es_la_misma_de_la_hoja_de_estilos(estilos, constante, variable):
    assert constante.lower() == _variable(estilos, variable)


def test_la_hoja_de_estilos_no_usa_el_azul_de_bootstrap(estilos):
    # Los comentarios pueden nombrarlo para explicar qué se reemplaza.
    reglas = re.sub(r"/\*.*?\*/", "", estilos, flags=re.DOTALL)
    for azul in AZULES_DE_BOOTSTRAP:
        assert azul not in reglas


@pytest.mark.parametrize(
    "variable",
    [
        "--bs-primary:",
        "--bs-primary-rgb:",
        "--bs-link-color:",
        "--bs-link-color-rgb:",
        "--bs-focus-ring-color:",
    ],
)
def test_las_variables_de_color_de_bootstrap_estan_reemplazadas(estilos, variable):
    """Sin estos reemplazos, enlaces, pestañas y anillos de foco salen en el azul de Bootstrap."""
    assert variable in estilos


def test_las_casillas_y_los_interruptores_usan_el_color_de_la_plataforma(estilos):
    regla = estilos[estilos.index(".form-check-input:checked") :]
    assert "var(--teal)" in regla[: regla.index("}")]


def test_sin_numeral_entrega_el_formato_de_openpyxl():
    assert paleta.sin_numeral("#15616D") == "15616D"
