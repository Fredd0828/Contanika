"""Filtros de plantilla del módulo 6: formato de valores en pesos colombianos."""

from decimal import ROUND_HALF_UP, Decimal

from django import template

register = template.Library()


def formato_pesos(valor):
    """
    Formatea un valor en pesos colombianos sin decimales y con punto como
    separador de miles, por ejemplo `1200000` → `$ 1.200.000`.
    """
    entero = int(Decimal(valor or 0).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    signo = "-" if entero < 0 else ""
    return f"{signo}$ {abs(entero):,}".replace(",", ".")


@register.filter(name="pesos")
def pesos(valor):
    """Filtro `{{ valor|pesos }}` para mostrar montos en las plantillas."""
    return formato_pesos(valor)
