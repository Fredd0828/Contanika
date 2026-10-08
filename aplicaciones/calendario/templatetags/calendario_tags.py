"""Filtros de plantilla del módulo 2: acceso a eventos por fecha y estilos."""

from django import template

register = template.Library()

COLORES_AMBITO = {
    "Nacional": "ev-nacional",
    "Distrital": "ev-distrital",
    "Municipal": "ev-municipal",
}

COLORES_ESTADO = {
    "Pendiente": "ev-pendiente",
    "En progreso": "ev-progreso",
    "Presentada": "ev-presentada",
}


@register.filter
def eventos_del_dia(eventos, fecha):
    """Devuelve los eventos registrados en una fecha concreta."""
    return eventos.get(fecha, [])


@register.filter
def clase_evento(evento):
    """Clase CSS del evento según su tipo, origen (tributario/tarea) y estado."""
    if evento["tipo"] == "anotacion":
        return "ev-anotacion"
    vencimiento = evento["objeto"]
    if vencimiento.tarea_id:
        clases = ["ev-tarea"]
    else:
        clases = [COLORES_AMBITO.get(vencimiento.ambito, "ev-nacional")]
    clases.append(COLORES_ESTADO.get(vencimiento.estado_presentacion, "ev-pendiente"))
    return " ".join(clases)


@register.filter
def url_evento(evento):
    """URL de destino al hacer clic en un evento del calendario."""
    if evento["tipo"] == "vencimiento":
        from django.urls import reverse

        return reverse("calendario:detalle", kwargs={"pk": evento["objeto"].pk})
    return ""


@register.filter
def titulo_evento(evento):
    """Texto corto que se muestra dentro de la celda del día."""
    if evento["tipo"] == "anotacion":
        return evento["objeto"].contenido[:40]
    vencimiento = evento["objeto"]
    prefijo = "Tarea: " if vencimiento.tarea_id else ""
    return f"{prefijo}{vencimiento.cliente.nombre_razon_social} · {vencimiento.tipo_obligacion}"
