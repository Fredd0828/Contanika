"""Pruebas del modelo y los servicios del módulo 9: expediente y bitácora."""

from datetime import date

import pytest
from django.utils import timezone

from aplicaciones.comunes.models import Adjunto
from aplicaciones.expediente import servicios
from aplicaciones.expediente.models import Anotacion

from .conftest import archivo_prueba

pytestmark = pytest.mark.django_db


def test_fecha_por_defecto_es_hoy_y_fecha_hora_es_automatica(cliente, usuario_administrador):
    anotacion = Anotacion.objects.create(
        cliente=cliente,
        usuario=usuario_administrador,
        tipo_anotacion="Llamada",
        contenido="Llamada de control.",
    )
    assert anotacion.fecha == timezone.localdate()
    assert anotacion.fecha_hora is not None


def test_eliminar_anotacion_la_archiva_sin_borrarla(anotacion_cliente):
    anotacion_cliente.delete()
    anotacion_cliente.refresh_from_db()
    assert anotacion_cliente.archivado is True


def test_restaurar_devuelve_la_anotacion(anotacion_cliente):
    anotacion_cliente.archivar()
    anotacion_cliente.restaurar()
    anotacion_cliente.refresh_from_db()
    assert anotacion_cliente.archivado is False


def test_orden_por_fecha_del_evento_mas_reciente_primero(cliente, usuario_administrador):
    antigua = Anotacion.objects.create(
        cliente=cliente,
        usuario=usuario_administrador,
        tipo_anotacion="Hito",
        fecha=date(2026, 1, 5),
        contenido="a",
    )
    reciente = Anotacion.objects.create(
        cliente=cliente,
        usuario=usuario_administrador,
        tipo_anotacion="Hito",
        fecha=date(2026, 6, 5),
        contenido="b",
    )
    assert list(Anotacion.objects.all()) == [reciente, antigua]


def test_crear_anotacion_con_adjuntos(cliente, usuario_senior):
    anotacion = servicios.crear_anotacion(
        cliente=cliente,
        usuario=usuario_senior,
        tipo_anotacion="Entrega de documento",
        fecha=date(2026, 9, 30),
        contenido="El cliente entregó extractos bancarios.",
        archivos=[archivo_prueba("extracto.pdf"), archivo_prueba("anexo.pdf")],
    )
    assert anotacion.usuario == usuario_senior
    adjuntos = Adjunto.objects.filter(tabla_origen=Adjunto.ANOTACION, id_origen=anotacion.pk)
    assert sorted(adjuntos.values_list("nombre_archivo", flat=True)) == ["anexo.pdf", "extracto.pdf"]
    adjunto = adjuntos.first()
    assert adjunto.archivo.name.startswith("adjuntos/anotaciones/")
    assert adjunto.archivo.read().startswith(b"%PDF")


def test_crear_anotacion_sin_adjuntos(cliente, usuario_administrador):
    anotacion = servicios.crear_anotacion(
        cliente=cliente,
        usuario=usuario_administrador,
        tipo_anotacion="Acuerdo",
        fecha=date(2026, 9, 30),
        contenido="Se acordó el envío mensual de soportes.",
    )
    assert not Adjunto.objects.filter(tabla_origen=Adjunto.ANOTACION, id_origen=anotacion.pk).exists()


def test_adjuntos_de_hallazgo_siguen_en_su_carpeta(cliente):
    adjunto = Adjunto.objects.create(
        tabla_origen=Adjunto.HALLAZGO, id_origen=1, archivo=archivo_prueba(), nombre_archivo="soporte.pdf"
    )
    assert adjunto.archivo.name.startswith("adjuntos/hallazgos/")


def test_archivar_y_restaurar_por_servicio(anotacion_cliente):
    servicios.archivar_anotacion(anotacion_cliente)
    anotacion_cliente.refresh_from_db()
    assert anotacion_cliente.archivado is True
    servicios.restaurar_anotacion(anotacion_cliente)
    anotacion_cliente.refresh_from_db()
    assert anotacion_cliente.archivado is False
