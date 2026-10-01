"""
Consultas reutilizables del módulo 7: comunicaciones integradas.

Se separan de las vistas para reutilizarse en el historial general, el
historial de un cliente y el panel dentro de su ficha.
"""

from aplicaciones.clientes.models import Cliente

from .models import Comunicacion


def clientes_visibles(usuario):
    """Clientes cuyo historial puede consultar el usuario (HU021-1: el Junior, solo los suyos)."""
    consulta = Cliente.objects.all()
    if usuario.es_contador_junior:
        consulta = consulta.filter(responsable=usuario)
    return consulta


def comunicaciones_visibles(usuario):
    """Comunicaciones de los clientes visibles para el usuario."""
    consulta = Comunicacion.objects.select_related("cliente", "usuario")
    if usuario.es_contador_junior:
        consulta = consulta.filter(cliente__responsable=usuario)
    return consulta


def filtrar_comunicaciones(usuario, cliente=None, canal=None, tipo=None, desde=None, hasta=None):
    """Aplica los filtros desplegables del historial; todos son opcionales."""
    consulta = comunicaciones_visibles(usuario)
    if cliente:
        consulta = consulta.filter(cliente=cliente)
    if canal:
        consulta = consulta.filter(canal__iexact=canal)
    if tipo:
        consulta = consulta.filter(tipo=tipo)
    if desde:
        consulta = consulta.filter(fecha_hora__date__gte=desde)
    if hasta:
        consulta = consulta.filter(fecha_hora__date__lte=hasta)
    return consulta


def canales(usuario):
    """Canales sugeridos más los ya usados en el historial, sin repetir."""
    usados = comunicaciones_visibles(usuario).values_list("canal", flat=True).distinct().order_by("canal")
    lista = list(Comunicacion.CANALES_SUGERIDOS)
    conocidos = {canal.lower() for canal in lista}
    for canal in usados:
        if canal.lower() not in conocidos:
            lista.append(canal)
            conocidos.add(canal.lower())
    return lista


def comunicaciones_del_cliente(usuario, cliente, limite=10):
    """Últimas comunicaciones del cliente, para el panel en su ficha."""
    return filtrar_comunicaciones(usuario, cliente=cliente)[:limite]
