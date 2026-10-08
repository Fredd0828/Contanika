"""
Consultas reutilizables del módulo 5: hallazgos y revisiones contables.

Se separan de las vistas para reutilizarse en el listado, el detalle del
hallazgo y el panel dentro de la ficha del cliente.
"""

from aplicaciones.comunes.models import Adjunto

from .models import Hallazgo


def hallazgos_visibles(usuario):
    """
    Hallazgos que el usuario puede consultar.

    Todos los roles ven los hallazgos de todos los clientes, para trabajar con
    la misma información del equipo (decisión del usuario, 1-oct-2026). Que el
    Contador Junior pueda ver un hallazgo no le permite modificarlo: ver
    `hallazgos_gestionables`.
    """
    return Hallazgo.objects.select_related("cliente", "responsable")


def hallazgos_gestionables(usuario):
    """Hallazgos que el usuario puede editar, cambiar de estado o adjuntar (el Junior, solo los suyos)."""
    consulta = hallazgos_visibles(usuario)
    if usuario.es_contador_junior:
        consulta = consulta.filter(cliente__responsable=usuario)
    return consulta


def clientes_para_hallazgos(usuario):
    """Clientes activos disponibles para registrar un hallazgo."""
    from aplicaciones.clientes.models import Cliente

    consulta = Cliente.objects.filter(estado=Cliente.ACTIVO)
    if usuario.es_contador_junior:
        consulta = consulta.filter(responsable=usuario)
    return consulta


def filtrar_hallazgos(usuario, tipo=None, estado=None, responsable=None, desde=None, hasta=None):
    """
    Aplica los filtros desplegables del listado; todos son opcionales.

    El rango de fechas busca por traslape con el período revisado: un hallazgo
    aparece si su período (inicio a fin) se cruza con el rango consultado, por
    ejemplo un período de enero a junio aparece al buscar solo marzo.
    """
    consulta = hallazgos_visibles(usuario)
    if tipo:
        consulta = consulta.filter(tipo_hallazgo=tipo)
    if estado:
        consulta = consulta.filter(estado=estado)
    if responsable:
        consulta = consulta.filter(responsable=responsable)
    if desde:
        consulta = consulta.filter(fecha_fin_periodo__gte=desde)
    if hasta:
        consulta = consulta.filter(fecha_inicio_periodo__lte=hasta)
    return consulta


def opciones_filtro_hallazgos(usuario):
    """Tipos de hallazgo ya registrados, para sugerirlos en el filtro abierto."""
    tipos = (
        hallazgos_visibles(usuario)
        .exclude(tipo_hallazgo="")
        .values_list("tipo_hallazgo", flat=True)
        .distinct()
        .order_by("tipo_hallazgo")
    )
    return {"tipos_hallazgo": list(tipos)}


def adjuntos_del_hallazgo(hallazgo):
    """Archivos de soporte cargados para este hallazgo, más recientes primero."""
    return Adjunto.objects.filter(tabla_origen=Adjunto.HALLAZGO, id_origen=hallazgo.pk).order_by(
        "-fecha_carga"
    )


def hallazgos_del_cliente(usuario, cliente, limite=10):
    """Últimos hallazgos del cliente, para el panel en su ficha."""
    return hallazgos_visibles(usuario).filter(cliente=cliente)[:limite]
