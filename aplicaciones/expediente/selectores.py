"""
Consultas reutilizables del módulo 9: expediente y bitácora por cliente.

Se separan de las vistas para reutilizarse en la bitácora general, el
expediente de un cliente y el panel dentro de su ficha.
"""

from aplicaciones.clientes.models import Cliente
from aplicaciones.comunes.models import Adjunto

from .models import Anotacion


def clientes_visibles(usuario):
    """
    Clientes cuyo expediente puede consultar y anotar el usuario.

    El Contador Junior solo accede a sus clientes asignados (HU027-1); los
    demás roles acceden a todos, incluidos los inactivos, porque su historial
    se conserva.
    """
    consulta = Cliente.objects.all()
    if usuario.es_contador_junior:
        consulta = consulta.filter(responsable=usuario)
    return consulta


def anotaciones_visibles(usuario):
    """Anotaciones de los clientes visibles para el usuario (HU027-5: no solo las propias)."""
    consulta = Anotacion.objects.select_related("cliente", "usuario")
    if usuario.es_contador_junior:
        consulta = consulta.filter(cliente__responsable=usuario)
    return consulta


def filtrar_anotaciones(usuario, cliente=None, tipo=None, desde=None, hasta=None, incluir_archivadas=False):
    """
    Aplica los filtros desplegables del expediente; todos son opcionales.

    El rango compara contra la fecha del evento anotado, para responder
    preguntas como «¿se presentó la retención hace seis meses?». Las
    anotaciones archivadas se ocultan salvo que se pidan expresamente.
    """
    consulta = anotaciones_visibles(usuario)
    if cliente:
        consulta = consulta.filter(cliente=cliente)
    if tipo:
        consulta = consulta.filter(tipo_anotacion__iexact=tipo)
    if desde:
        consulta = consulta.filter(fecha__gte=desde)
    if hasta:
        consulta = consulta.filter(fecha__lte=hasta)
    if not incluir_archivadas:
        consulta = consulta.filter(archivado=False)
    return consulta


def tipos_de_anotacion(usuario):
    """Tipos sugeridos por el spec más los ya escritos por el equipo, sin repetir."""
    usados = (
        anotaciones_visibles(usuario)
        .values_list("tipo_anotacion", flat=True)
        .distinct()
        .order_by("tipo_anotacion")
    )
    tipos = list(Anotacion.TIPOS_SUGERIDOS)
    conocidos = {tipo.lower() for tipo in tipos}
    for tipo in usados:
        if tipo.lower() not in conocidos:
            tipos.append(tipo)
            conocidos.add(tipo.lower())
    return tipos


def con_adjuntos(anotaciones):
    """
    Carga los adjuntos de una página de anotaciones con una sola consulta.

    `Adjunto` no tiene FK real hacia `Anotacion` (usa `tabla_origen`/
    `id_origen`), así que no sirve `prefetch_related`; cada anotación recibe
    su lista en el atributo `lista_adjuntos`.
    """
    anotaciones = list(anotaciones)
    por_anotacion = {anotacion.pk: [] for anotacion in anotaciones}
    adjuntos = Adjunto.objects.filter(tabla_origen=Adjunto.ANOTACION, id_origen__in=por_anotacion).order_by(
        "fecha_carga"
    )
    for adjunto in adjuntos:
        por_anotacion[adjunto.id_origen].append(adjunto)
    for anotacion in anotaciones:
        anotacion.lista_adjuntos = por_anotacion[anotacion.pk]
    return anotaciones


def anotaciones_del_cliente(usuario, cliente, limite=10):
    """Últimas anotaciones vigentes del cliente, para el panel en su ficha."""
    return con_adjuntos(filtrar_anotaciones(usuario, cliente=cliente)[:limite])
