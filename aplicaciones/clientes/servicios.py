"""
Reglas de negocio del módulo 1: guardado e inactivación de clientes.

Las vistas no escriben directamente en varios modelos: llaman a estas
funciones, que agrupan la operación en una transacción para que la ficha,
los municipios adicionales y los tipos de servicio queden consistentes.
"""

from django.db import transaction
from django.utils import timezone

from .models import ClienteServicio


@transaction.atomic
def guardar_cliente(formulario, formset_municipios, usuario):
    """
    Guarda la ficha del cliente, sus municipios adicionales y sus servicios.

    Si el usuario no asigna un responsable, queda el usuario que registra el
    cliente. Devuelve el cliente guardado.
    """
    cliente = formulario.save(commit=False)
    if not cliente.pk:
        cliente.fecha_registro = timezone.localdate()
    if not cliente.responsable_id:
        cliente.responsable = usuario
    cliente.save()

    formset_municipios.instance = cliente
    formset_municipios.save()

    _sincronizar_servicios(cliente, formulario.servicios_seleccionados())
    return cliente


def _sincronizar_servicios(cliente, tipos_servicio):
    """Deja registrados exactamente los tipos de servicio marcados."""
    ClienteServicio.objects.filter(cliente=cliente).exclude(tipo_servicio__in=tipos_servicio).delete()
    for tipo in tipos_servicio:
        ClienteServicio.objects.get_or_create(cliente=cliente, tipo_servicio=tipo)


@transaction.atomic
def inactivar_cliente(cliente):
    """
    Inactiva al cliente conservando su historial.

    El cliente no se elimina: queda con estado Inactivo y disponible para
    consulta en los demás módulos del sistema.
    """
    cliente.inactivar()
    return cliente
