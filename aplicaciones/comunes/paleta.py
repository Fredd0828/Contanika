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
TEAL_OSCURO = "#0D4A54"
TEAL_SUAVE = "#E0F0F2"
MARRON = "#78290F"
CREMA_SUAVE = "#FFF6E8"
BORDE_SUAVE = "#E2E8ED"
SUPERFICIE = "#F8FAFB"
TEXTO_TENUE = "#2A4A5A"
TEXTO_APAGADO = "#7A6A58"
TINTE_ROJO = "#FDEAEA"

# Series de los gráficos, en orden: principal, positivo, advertencia y riesgo.
SERIES_GRAFICO = [TEAL, VERDE, NARANJA, ROJO]


def sin_numeral(color):
    """Color en el formato que pide openpyxl: hexadecimal sin el `#` inicial."""
    return color.lstrip("#")
