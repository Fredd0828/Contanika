"""
Consultas del módulo 2: vencimientos y anotaciones visibles para cada usuario.

Se separan de las vistas para reutilizarse en el calendario, el listado, el
detalle del cliente y el futuro reporte de vencimientos (Módulo 10).
"""

from django.db.models import Q

from .models import (
    AnotacionCalendario,
    ConfiguracionAlerta,
    TablaReferenciaDian,
    Vencimiento,
)


def vencimientos_visibles(usuario):
    """
    Vencimientos que el usuario puede ver según su rol.

    El Contador Junior solo ve los vencimientos de los clientes que tiene
    asignados; los demás roles ven todos.
    """
    consulta = Vencimiento.objects.select_related("cliente", "responsable").prefetch_related("alertas")
    if usuario.es_contador_junior:
        consulta = consulta.filter(cliente__responsable=usuario)
    return consulta


def filtrar_vencimientos(
    usuario,
    fecha_inicio=None,
    fecha_fin=None,
    cliente=None,
    ambito=None,
    estado_presentacion=None,
    tipo_obligacion=None,
    responsable=None,
):
    """
    Aplica los filtros desplegables del calendario y del listado.

    Todos los filtros son opcionales; la consulta base ya respeta la
    visibilidad por rol (Junior solo sus clientes asignados).
    """
    consulta = vencimientos_visibles(usuario)
    if fecha_inicio:
        consulta = consulta.filter(fecha_vencimiento__gte=fecha_inicio)
    if fecha_fin:
        consulta = consulta.filter(fecha_vencimiento__lte=fecha_fin)
    if cliente:
        consulta = consulta.filter(cliente_id=cliente)
    if ambito:
        consulta = consulta.filter(ambito=ambito)
    if estado_presentacion:
        consulta = consulta.filter(estado_presentacion=estado_presentacion)
    if tipo_obligacion:
        consulta = consulta.filter(tipo_obligacion=tipo_obligacion)
    if responsable:
        consulta = consulta.filter(responsable_id=responsable)
    return consulta


def vencimientos_por_cliente(usuario, cliente):
    """
    Vencimientos de un cliente concreto, respetando la visibilidad por rol.

    Si un Contador Junior intenta consultar un cliente que no tiene asignado,
    la consulta devuelve vacío y la vista responderá 404.
    """
    return filtrar_vencimientos(usuario, cliente=cliente.pk)


def anotaciones_visibles(usuario, fecha_inicio=None, fecha_fin=None):
    """
    Anotaciones del calendario visibles para el usuario.

    - Privadas: solo el autor.
    - Equipo completo: todos.
    - Por rol: usuarios con el mismo rol del autor.
    - Por etiqueta: solo los usuarios destinatarios (y el autor).
    """
    base = AnotacionCalendario.objects.select_related("autor").prefetch_related("destinatarios__usuario")
    visibles = base.filter(
        Q(visibilidad=AnotacionCalendario.EQUIPO)
        | Q(autor=usuario)
        | Q(visibilidad=AnotacionCalendario.POR_ROL, autor__rol=usuario.rol)
        | Q(visibilidad=AnotacionCalendario.POR_ETIQUETA, destinatarios__usuario=usuario)
    ).distinct()

    if fecha_inicio:
        visibles = visibles.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        visibles = visibles.filter(fecha__lte=fecha_fin)
    return visibles


def opciones_filtro_calendario():
    """
    Valores para llenar los filtros desplegables del calendario y del listado.

    El tipo de obligación es una selección abierta: se sugieren los valores ya
    registrados en vencimientos y en la tabla de referencia DIAN, pero el
    usuario puede escribir uno nuevo.
    """
    tipos_vencimiento = Vencimiento.objects.values_list("tipo_obligacion", flat=True).distinct()
    tipos_dian = TablaReferenciaDian.objects.values_list("tipo_obligacion", flat=True).distinct()

    return {
        "tipos_obligacion": sorted(set(tipos_vencimiento) | set(tipos_dian)),
        "ambitos": Vencimiento.OPCIONES_AMBITO,
        "estados_presentacion": Vencimiento.OPCIONES_ESTADO_PRESENTACION,
        "estados_validacion": Vencimiento.OPCIONES_ESTADO_VALIDACION,
        "canales_alerta": ConfiguracionAlerta.OPCIONES_CANAL,
        "visibilidades_anotacion": AnotacionCalendario.OPCIONES_VISIBILIDAD,
    }
