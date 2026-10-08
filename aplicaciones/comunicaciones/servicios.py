"""Operaciones de escritura del módulo 7: comunicaciones integradas."""

from .models import Comunicacion


def registrar_comunicacion_manual(cliente, usuario, canal, fecha_hora, contenido_resumen):
    """
    Registra un contacto hecho por fuera de la plataforma (llamada, reunión
    presencial u otro canal), en el mismo historial que las automáticas
    (HU019-2). Las comunicaciones no se editan ni se eliminan.
    """
    return Comunicacion.objects.create(
        cliente=cliente,
        usuario=usuario,
        canal=canal,
        tipo=Comunicacion.MANUAL,
        fecha_hora=fecha_hora,
        contenido_resumen=contenido_resumen,
        estado_envio=Comunicacion.EXITO,
        modulo_origen=Comunicacion.ORIGEN_MANUAL,
    )
