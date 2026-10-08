"""
Estructura común del resultado de un reporte del módulo 10.

Cada reporte arma un `ResultadoReporte` con sus secciones (tablas), un
resumen de indicadores y, si aplica, un gráfico. La misma estructura se
pinta en pantalla y se exporta a Excel o PDF, así los tres formatos muestran
siempre la misma información.
"""

from dataclasses import dataclass, field

# Tipos de columna: definen el formato en pantalla, Excel y PDF.
TEXTO = "texto"
PESOS = "pesos"
FECHA = "fecha"
NUMERO = "numero"
PORCENTAJE = "porcentaje"


@dataclass
class Columna:
    titulo: str
    tipo: str = TEXTO
    ancho: int = 18  # ancho aproximado en caracteres (Excel y proporción en PDF)


@dataclass
class Seccion:
    """Una tabla del reporte; las filas en `resaltadas` se marcan en rojo."""

    titulo: str
    columnas: list
    filas: list = field(default_factory=list)
    resaltadas: set = field(default_factory=set)
    nota_resaltado: str = ""


@dataclass
class Grafico:
    """Gráfico de barras: una etiqueta por categoría y una o varias series."""

    titulo: str
    etiquetas: list
    series: list  # [(nombre, [valores])]
    horizontal: bool = False


@dataclass
class ResultadoReporte:
    secciones: list
    resumen: list = field(default_factory=list)  # [(etiqueta, valor ya formateado)]
    grafico: Grafico | None = None
    notas: list = field(default_factory=list)

    @property
    def total_filas(self):
        return sum(len(seccion.filas) for seccion in self.secciones)
