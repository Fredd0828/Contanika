"""Pruebas de los servicios del módulo 5: hallazgos y revisiones contables."""

from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from aplicaciones.comunes.models import Adjunto
from aplicaciones.hallazgos import servicios
from aplicaciones.hallazgos.models import Hallazgo

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_root_temporal(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def hallazgo(cliente):
    return Hallazgo.objects.create(
        cliente=cliente,
        tipo_hallazgo="Inconsistencia",
        fecha_inicio_periodo=date(2026, 1, 1),
        fecha_fin_periodo=date(2026, 1, 31),
        descripcion="Diferencia detectada en la conciliación bancaria.",
    )


def test_cambiar_estado_a_cerrado_usa_metodo_cerrar_del_modelo(hallazgo):
    servicios.cambiar_estado_hallazgo(hallazgo, Hallazgo.CERRADO, "Se aclaró con el cliente.")
    hallazgo.refresh_from_db()
    assert hallazgo.estado == Hallazgo.CERRADO
    assert hallazgo.observacion_cierre == "Se aclaró con el cliente."


def test_cambiar_estado_a_otro_valor_no_toca_observacion(hallazgo):
    hallazgo.observacion_cierre = "Cierre anterior."
    hallazgo.estado = Hallazgo.CERRADO
    hallazgo.save()

    servicios.cambiar_estado_hallazgo(hallazgo, Hallazgo.EN_PROCESO)
    hallazgo.refresh_from_db()
    assert hallazgo.estado == Hallazgo.EN_PROCESO
    assert hallazgo.observacion_cierre == "Cierre anterior."


def _archivo_prueba(nombre="soporte.pdf"):
    return SimpleUploadedFile(nombre, b"%PDF-contenido-de-prueba", content_type="application/pdf")


def test_agregar_adjunto_crea_fila_con_archivo_real(hallazgo):
    adjunto = servicios.agregar_adjunto(hallazgo, _archivo_prueba())
    assert adjunto.tabla_origen == Adjunto.HALLAZGO
    assert adjunto.id_origen == hallazgo.pk
    assert adjunto.nombre_archivo == "soporte.pdf"
    assert adjunto.archivo.read().startswith(b"%PDF")


def test_eliminar_adjunto_borra_archivo_fisico_y_fila(hallazgo):
    adjunto = servicios.agregar_adjunto(hallazgo, _archivo_prueba())
    ruta_archivo = adjunto.archivo.path
    servicios.eliminar_adjunto(adjunto)
    assert not Adjunto.objects.filter(pk=adjunto.pk).exists()
    import os

    assert not os.path.exists(ruta_archivo)


def test_eliminar_hallazgo_borra_sus_adjuntos_y_archivos(hallazgo):
    adjunto_1 = servicios.agregar_adjunto(hallazgo, _archivo_prueba("uno.pdf"))
    adjunto_2 = servicios.agregar_adjunto(hallazgo, _archivo_prueba("dos.pdf"))
    rutas = [adjunto_1.archivo.path, adjunto_2.archivo.path]

    servicios.eliminar_hallazgo(hallazgo)

    import os

    assert not Hallazgo.objects.filter(pk=hallazgo.pk).exists()
    assert Adjunto.objects.filter(tabla_origen=Adjunto.HALLAZGO, id_origen=hallazgo.pk).count() == 0
    assert not any(os.path.exists(ruta) for ruta in rutas)
