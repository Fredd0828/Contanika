"""
Paleta de colores de Contanika para lo que se genera fuera del navegador:
PDF (ReportLab), Excel (openpyxl) y gráficos.

Son los mismos colores de `estaticos/css/contanika.css` (variables `--navy`,
`--teal`, `--orange`…). Si la paleta cambia allá, se cambia también aquí para
que los documentos descargados se vean como la plataforma.
"""

NAVY = "#001524"
TEAL = "#15616D"
TEAL_CLARO = "#7FB5BD"
NARANJA = "#FF7D00"
VERDE = "#0A8A5C"
ROJO = "#E05252"
CREMA = "#FFECD1"
BORDE = "#D0DAE2"

# Series de los gráficos, en orden: principal, positivo, advertencia y riesgo.
SERIES_GRAFICO = [TEAL, VERDE, NARANJA, ROJO]


def sin_numeral(color):
    """Color en el formato que pide openpyxl: hexadecimal sin el `#` inicial."""
    return color.lstrip("#")
