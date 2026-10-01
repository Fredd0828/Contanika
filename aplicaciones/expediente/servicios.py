"""Operaciones de escritura del módulo 9: expediente y bitácora por cliente."""

from django.db import transaction

from aplicaciones.comunes.models import Adjunto

from .models import Anotacion


@transaction.atomic
def crear_anotacion(cliente, usuario, tipo_anotacion, fecha, contenido, archivos=()):
    """
    Registra una anotación con sus archivos de soporte.

    El usuario y la fecha y hora exacta quedan fijados por el sistema
    (HU025-2); después de guardada la anotación no se edita ni se elimina.
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


def archivar_anotacion(anotacion):
    """Oculta la anotación del expediente sin borrarla (solo el Administrador)."""
    anotacion.archivar()
    return anotacion


def restaurar_anotacion(anotacion):
    """Devuelve al expediente una anotación archivada (solo el Administrador)."""
    anotacion.restaurar()
    return anotacion
