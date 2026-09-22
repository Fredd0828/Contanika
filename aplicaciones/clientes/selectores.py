"""
Consultas del módulo 1: filtrado del listado y opciones de los filtros.

Los filtros se separan de las vistas para que la consulta sea reutilizable
por el listado, la exportación y el futuro reporte de clientes (Módulo 10).
"""

from django.db.models import Q

from .models import Cliente
from .municipios_colombia import MUNICIPIOS_COLOMBIA

REGIMENES_BASE = [
    "No responsable",
    "Régimen ordinario",
    "Régimen simple de tributación",
]


def filtrar_clientes(
    ciudad=None,
    municipio=None,
    regimen_tributario=None,
    tipo_persona=None,
    tipo_documento=None,
    responsable=None,
    estado=None,
):
    """
    Devuelve los clientes que cumplen los filtros desplegables del listado.

    El filtro por municipio cubre tanto el municipio principal como los
    municipios adicionales registrados para el multi-ICA del cliente.
    """
    consulta = Cliente.objects.select_related("responsable").prefetch_related(
        "servicios__tipo_servicio", "municipios_adicionales"
    )
    if ciudad:
        consulta = consulta.filter(ciudad=ciudad)
    if municipio:
        consulta = consulta.filter(
            Q(municipio_principal=municipio) | Q(municipios_adicionales__municipio=municipio)
        ).distinct()
    if regimen_tributario:
        consulta = consulta.filter(regimen_tributario=regimen_tributario)
    if tipo_persona:
        consulta = consulta.filter(tipo_persona=tipo_persona)
    if tipo_documento:
        consulta = consulta.filter(tipo_documento=tipo_documento)
    if responsable:
        consulta = consulta.filter(responsable_id=responsable)
    if estado:
        consulta = consulta.filter(estado=estado)
    return consulta


def opciones_filtro():
    """
    Valores para llenar los filtros desplegables y datalists.

    Combina una lista base de municipios de Colombia y regímenes comunes
    con los valores ya registrados en el sistema, de modo que los filtros
    crezcan con el portafolio real del despacho.
    """

    def valores(campo):
        return (
            Cliente.objects.exclude(**{f"{campo}__exact": ""})
            .values_list(campo, flat=True)
            .distinct()
            .order_by(campo)
        )

    ciudades_registradas = set(valores("ciudad"))
    municipios_registrados = set(valores("municipio_principal"))
    regimenes_registrados = set(valores("regimen_tributario"))

    return {
        "ciudades": sorted(ciudades_registradas | set(MUNICIPIOS_COLOMBIA)),
        "municipios": sorted(municipios_registrados | set(MUNICIPIOS_COLOMBIA)),
        "regimenes": sorted(regimenes_registrados | set(REGIMENES_BASE)),
        "tipos_documento": Cliente.OPCIONES_TIPO_DOCUMENTO,
    }
