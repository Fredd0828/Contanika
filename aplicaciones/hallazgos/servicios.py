"""Operaciones de escritura del módulo 5: hallazgos y revisiones contables."""

from django.db import transaction

from aplicaciones.comunes.models import Adjunto

from . import selectores
from .models import Hallazgo


def crear_hallazgo(formulario):
    """Registra un nuevo hallazgo a partir de un `HallazgoForm` ya validado."""
    return formulario.save()


def actualizar_hallazgo(hallazgo, formulario):
    """Actualiza los datos de registro de un hallazgo ya validado."""
    return formulario.save()


@transaction.atomic
def cambiar_estado_hallazgo(hallazgo, estado, observacion_cierre=""):
    """
    Cambia el estado del hallazgo.

    Si el estado destino es "Cerrado", reutiliza `Hallazgo.cerrar` para dejar
    registrada la observación de cierre exigida por el spec.
    """
    if estado == Hallazgo.CERRADO:
        hallazgo.cerrar(observacion_cierre)
    else:
        hallazgo.estado = estado
        hallazgo.save(update_fields=["estado"])
    return hallazgo


@transaction.atomic
def eliminar_hallazgo(hallazgo):
    """
    Elimina el hallazgo y sus adjuntos.

    `Adjunto` no tiene una FK real hacia `Hallazgo` (usa `tabla_origen`/
    `id_origen`), así que sus archivos físicos y filas se borran a mano
    antes de borrar el hallazgo.
    """
    for adjunto in selectores.adjuntos_del_hallazgo(hallazgo):
        eliminar_adjunto(adjunto)
    hallazgo.delete()


def agregar_adjunto(hallazgo, archivo):
    """Guarda un archivo de soporte cargado para el hallazgo."""
    return Adjunto.objects.create(
        tabla_origen=Adjunto.HALLAZGO,
        id_origen=hallazgo.pk,
        archivo=archivo,
        nombre_archivo=archivo.name,
    )


def eliminar_adjunto(adjunto):
    """Borra el archivo físico y la fila del adjunto."""
    adjunto.archivo.delete(save=False)
    adjunto.delete()
