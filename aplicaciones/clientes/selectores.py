"""
Consultas del módulo 1: filtrado del listado y opciones de los filtros.

Los filtros se separan de las vistas para que la consulta sea reutilizable
por el listado, la exportación y el futuro reporte de clientes (Módulo 10).
"""

from .models import Cliente
from .municipios_colombia import MUNICIPIOS_COLOMBIA

REGIMENES_BASE = [
    "No responsable",
    "Régimen ordinario",
    "Régimen simple de tributación",
]


def filtrar_clientes(
    busqueda=None,
    nit=None,
    regimen_tributario=None,
    responsable_iva=None,
    estado=None,
):
    """
    Devuelve los clientes que cumplen los filtros desplegables del listado.

    `busqueda` filtra por coincidencia parcial en el nombre o razón social;
    `nit` filtra por coincidencia parcial en el número de documento.
    """
    consulta = Cliente.objects.select_related("responsable").prefetch_related(
        "servicios__tipo_servicio", "municipios_adicionales"
    )
    if busqueda:
        consulta = consulta.filter(nombre_razon_social__icontains=busqueda)
    if nit:
        consulta = consulta.filter(nit_cedula__icontains=nit)
    if regimen_tributario:
        consulta = consulta.filter(regimen_tributario=regimen_tributario)
    if responsable_iva:
        consulta = consulta.filter(responsable_iva=responsable_iva == "si")
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
