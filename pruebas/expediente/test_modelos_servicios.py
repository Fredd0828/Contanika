"""Pruebas del modelo y los servicios del módulo 9: expediente y bitácora."""

import pathlib
from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from aplicaciones.comunes.models import Adjunto
from aplicaciones.expediente import servicios
from aplicaciones.expediente.models import AccionAnotacion, Anotacion

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


def test_archivar_y_restaurar_por_servicio(anotacion_cliente, usuario_administrador):
    servicios.archivar_anotacion(anotacion_cliente, usuario_administrador)
    anotacion_cliente.refresh_from_db()
    assert anotacion_cliente.archivado is True
    servicios.restaurar_anotacion(anotacion_cliente, usuario_administrador)
    anotacion_cliente.refresh_from_db()
    assert anotacion_cliente.archivado is False
    acciones = list(AccionAnotacion.objects.order_by("id_accion").values_list("accion", flat=True))
    assert acciones == [AccionAnotacion.ARCHIVO, AccionAnotacion.RESTAURO]


# ---------------------------------------------------------------------------
# Editar y eliminar anotaciones archivadas (23-nov-2026)
# ---------------------------------------------------------------------------


def test_no_se_edita_ni_elimina_una_anotacion_vigente(anotacion_cliente, usuario_administrador):
    with pytest.raises(ValidationError, match="archivada"):
        servicios.editar_anotacion(
            anotacion_cliente, usuario_administrador, "Llamada", date(2026, 3, 1), "Otro"
        )
    with pytest.raises(ValidationError, match="archivada"):
        servicios.eliminar_anotacion(anotacion_cliente, usuario_administrador)
    assert Anotacion.objects.filter(pk=anotacion_cliente.pk).exists()
    assert not AccionAnotacion.objects.exists()


def test_editar_archivada_registra_lo_que_cambio(anotacion_cliente, usuario_administrador):
    servicios.archivar_anotacion(anotacion_cliente, usuario_administrador)
    servicios.editar_anotacion(
        anotacion_cliente, usuario_administrador, "Llamada", date(2026, 3, 12), "Texto corregido."
    )
    anotacion_cliente.refresh_from_db()
    assert (anotacion_cliente.tipo_anotacion, anotacion_cliente.contenido) == ("Llamada", "Texto corregido.")
    accion = AccionAnotacion.objects.get(accion=AccionAnotacion.EDITO)
    assert "«Retención en la fuente» → «Llamada»" in accion.detalle
    assert "10/03/2026 → 12/03/2026" in accion.detalle
    assert "Se presentó la retención en la fuente de febrero." in accion.detalle
    assert accion.usuario == usuario_administrador


def test_editar_sin_cambios_no_registra_nada(anotacion_cliente, usuario_administrador):
    servicios.archivar_anotacion(anotacion_cliente, usuario_administrador)
    servicios.editar_anotacion(
        anotacion_cliente,
        usuario_administrador,
        anotacion_cliente.tipo_anotacion,
        anotacion_cliente.fecha,
        anotacion_cliente.contenido,
    )
    assert not AccionAnotacion.objects.filter(accion=AccionAnotacion.EDITO).exists()


def test_eliminar_archivada_borra_anotacion_y_archivos_y_deja_constancia(
    anotacion_cliente, usuario_administrador, django_capture_on_commit_callbacks
):
    adjunto = Adjunto.objects.create(
        tabla_origen=Adjunto.ANOTACION,
        id_origen=anotacion_cliente.pk,
        archivo=archivo_prueba("acta.pdf"),
        nombre_archivo="acta.pdf",
    )
    ruta = pathlib.Path(adjunto.archivo.path)
    assert ruta.exists()
    servicios.archivar_anotacion(anotacion_cliente, usuario_administrador)
    with django_capture_on_commit_callbacks(execute=True):
        servicios.eliminar_anotacion(anotacion_cliente, usuario_administrador)

    assert not Anotacion.objects.filter(pk=anotacion_cliente.pk).exists()
    assert not Adjunto.objects.filter(pk=adjunto.pk).exists()
    assert not ruta.exists()
    eliminada = AccionAnotacion.objects.get(accion=AccionAnotacion.ELIMINO)
    assert eliminada.cliente == anotacion_cliente.cliente
    assert "Retención en la fuente del 10/03/2026" in eliminada.detalle
    assert "acta.pdf" in eliminada.detalle
    # El registro de cuando se archivó sigue ahí, sin la anotación.
    archivada = AccionAnotacion.objects.get(accion=AccionAnotacion.ARCHIVO)
    assert archivada.anotacion is None
