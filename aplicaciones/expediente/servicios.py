"""Operaciones de escritura del módulo 9: expediente y bitácora por cliente."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.formats import date_format
from django.utils.text import Truncator

from aplicaciones.comunes.models import Adjunto

from .models import AccionAnotacion, Anotacion

# Cuánto del contenido se copia en el registro de acciones.
LARGO_RESUMEN = 300


@transaction.atomic
def crear_anotacion(cliente, usuario, tipo_anotacion, fecha, contenido, archivos=()):
    """
    Registra una anotación con sus archivos de soporte.

    El usuario y la fecha y hora exacta quedan fijados por el sistema
    (HU025-2). Mientras esté vigente, la anotación no se edita ni se elimina.
    """
    anotacion = Anotacion.objects.create(
        cliente=cliente,
        usuario=usuario,
        tipo_anotacion=tipo_anotacion,
        fecha=fecha,
        contenido=contenido,
    )
    for archivo in archivos:
        Adjunto.objects.create(
            tabla_origen=Adjunto.ANOTACION,
            id_origen=anotacion.pk,
            archivo=archivo,
            nombre_archivo=archivo.name[:150],
        )
    return anotacion


def _resumen(anotacion):
    """Qué anotación era: tipo, fecha del evento y el comienzo del contenido."""
    contenido = Truncator(" ".join(anotacion.contenido.split())).chars(LARGO_RESUMEN)
    return f"{anotacion.tipo_anotacion} del {date_format(anotacion.fecha, 'd/m/Y')}: {contenido}"


def _registrar(anotacion, usuario, accion, detalle):
    return AccionAnotacion.objects.create(
        anotacion=anotacion if accion != AccionAnotacion.ELIMINO else None,
        cliente_id=anotacion.cliente_id,
        usuario=usuario,
        accion=accion,
        detalle=detalle,
    )


def _exigir_archivada(anotacion, que):
    if not anotacion.archivado:
        raise ValidationError(f"Solo se puede {que} una anotación archivada. Archívela primero.")


@transaction.atomic
def archivar_anotacion(anotacion, usuario):
    """Oculta la anotación del expediente sin borrarla (solo el Administrador)."""
    anotacion.archivar()
    _registrar(anotacion, usuario, AccionAnotacion.ARCHIVO, _resumen(anotacion))
    return anotacion


@transaction.atomic
def restaurar_anotacion(anotacion, usuario):
    """Devuelve al expediente una anotación archivada (solo el Administrador)."""
    anotacion.restaurar()
    _registrar(anotacion, usuario, AccionAnotacion.RESTAURO, _resumen(anotacion))
    return anotacion


@transaction.atomic
def editar_anotacion(anotacion, usuario, tipo_anotacion, fecha, contenido):
    """
    Corrige una anotación archivada (solo el Administrador). En el registro
    queda qué campos cambiaron y cómo era antes.
    """
    _exigir_archivada(anotacion, "editar")
    cambios = []
    if anotacion.tipo_anotacion != tipo_anotacion:
        cambios.append(f"Tipo: «{anotacion.tipo_anotacion}» → «{tipo_anotacion}»")
    if anotacion.fecha != fecha:
        cambios.append(f"Fecha: {date_format(anotacion.fecha, 'd/m/Y')} → {date_format(fecha, 'd/m/Y')}")
    if anotacion.contenido != contenido:
        anterior = Truncator(" ".join(anotacion.contenido.split())).chars(LARGO_RESUMEN)
        cambios.append(f"Contenido anterior: {anterior}")
    if not cambios:
        return anotacion
    anotacion.tipo_anotacion = tipo_anotacion
    anotacion.fecha = fecha
    anotacion.contenido = contenido
    anotacion.save(update_fields=["tipo_anotacion", "fecha", "contenido"])
    _registrar(anotacion, usuario, AccionAnotacion.EDITO, "\n".join(cambios))
    return anotacion


@transaction.atomic
def eliminar_anotacion(anotacion, usuario):
    """
    Borra de verdad una anotación archivada y sus archivos de soporte (solo
    el Administrador). Su resumen queda en el registro de acciones.
    """
    _exigir_archivada(anotacion, "eliminar")
    adjuntos = list(Adjunto.objects.filter(tabla_origen=Adjunto.ANOTACION, id_origen=anotacion.pk))
    detalle = _resumen(anotacion)
    if adjuntos:
        detalle += f"\nArchivos eliminados: {', '.join(adjunto.nombre_archivo for adjunto in adjuntos)}"
    _registrar(anotacion, usuario, AccionAnotacion.ELIMINO, detalle)
    archivos = [adjunto.archivo for adjunto in adjuntos]
    Adjunto.objects.filter(pk__in=[adjunto.pk for adjunto in adjuntos]).delete()
    # `Anotacion.delete()` archiva en vez de borrar: aquí se borra con el queryset.
    Anotacion.objects.filter(pk=anotacion.pk).delete()
    # Los archivos se borran del disco solo si la transacción se confirma.
    transaction.on_commit(lambda: [archivo.delete(save=False) for archivo in archivos])
