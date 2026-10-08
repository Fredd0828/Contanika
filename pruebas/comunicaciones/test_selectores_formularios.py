"""Pruebas de selectores, servicios y formularios del módulo 7: comunicaciones integradas."""

from datetime import date, timedelta

import pytest
from django.utils import timezone

from aplicaciones.comunicaciones import selectores, servicios
from aplicaciones.comunicaciones.formularios import ComunicacionManualForm, FiltroComunicacionesForm
from aplicaciones.comunicaciones.models import Comunicacion

from .conftest import momento

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Selectores
# ---------------------------------------------------------------------------


def test_junior_ve_las_comunicaciones_de_todos_los_clientes(
    usuario_junior, comunicacion_automatica, comunicacion_manual_junior
):
    assert set(selectores.comunicaciones_visibles(usuario_junior)) == {
        comunicacion_automatica,
        comunicacion_manual_junior,
    }


def test_senior_ve_todas_ordenadas_de_la_mas_reciente(
    usuario_senior, comunicacion_automatica, comunicacion_manual_junior
):
    assert list(selectores.comunicaciones_visibles(usuario_senior)) == [
        comunicacion_manual_junior,
        comunicacion_automatica,
    ]


def test_filtra_por_canal_tipo_y_fechas(
    usuario_administrador, comunicacion_automatica, comunicacion_manual_junior
):
    def filtrar(**filtros):
        return list(selectores.filtrar_comunicaciones(usuario_administrador, **filtros))

    assert filtrar(canal="llamada") == [comunicacion_manual_junior]
    assert filtrar(tipo=Comunicacion.AUTOMATICA) == [comunicacion_automatica]
    assert filtrar(desde=date(2026, 9, 1), hasta=date(2026, 9, 15)) == [comunicacion_automatica]
    assert filtrar(desde=date(2026, 9, 16)) == [comunicacion_manual_junior]


def test_canales_incluye_sugeridos_y_usados(usuario_administrador, cliente):
    Comunicacion.objects.create(cliente=cliente, canal="Videollamada", tipo=Comunicacion.MANUAL)
    canales = selectores.canales(usuario_administrador)
    assert canales[:4] == Comunicacion.CANALES_SUGERIDOS
    assert "Videollamada" in canales


# ---------------------------------------------------------------------------
# Servicio de registro manual
# ---------------------------------------------------------------------------


def test_registro_manual_queda_como_manual(cliente, usuario_senior):
    comunicacion = servicios.registrar_comunicacion_manual(
        cliente=cliente,
        usuario=usuario_senior,
        canal=Comunicacion.REUNION,
        fecha_hora=momento(2026, 9, 29, 15),
        contenido_resumen="Reunión de cierre de mes.",
    )
    assert comunicacion.tipo == Comunicacion.MANUAL
    assert comunicacion.modulo_origen == Comunicacion.ORIGEN_MANUAL
    assert comunicacion.fecha_hora == momento(2026, 9, 29, 15)
    assert not comunicacion.es_automatica


# ---------------------------------------------------------------------------
# Formularios
# ---------------------------------------------------------------------------


def _datos(cliente_pk, **extra):
    datos = {
        "cliente": cliente_pk,
        "canal": "  Llamada ",
        "fecha_hora": "2026-09-30T09:30",
        "contenido_resumen": "El cliente confirmó la reunión.",
    }
    datos.update(extra)
    return datos


def test_formulario_valido(usuario_administrador, cliente):
    formulario = ComunicacionManualForm(_datos(cliente.pk), usuario=usuario_administrador)
    assert formulario.is_valid(), formulario.errors
    assert formulario.cleaned_data["canal"] == "Llamada"


def test_formulario_propone_la_hora_actual(usuario_administrador):
    formulario = ComunicacionManualForm(usuario=usuario_administrador)
    assert formulario.initial["fecha_hora"].date() == timezone.localdate()


def test_formulario_acepta_canal_escrito(usuario_administrador, cliente):
    formulario = ComunicacionManualForm(
        _datos(cliente.pk, canal="Videollamada"), usuario=usuario_administrador
    )
    assert formulario.is_valid(), formulario.errors


def test_formulario_exige_resumen(usuario_administrador, cliente):
    formulario = ComunicacionManualForm(
        _datos(cliente.pk, contenido_resumen=""), usuario=usuario_administrador
    )
    assert not formulario.is_valid()
    assert "contenido_resumen" in formulario.errors


def test_formulario_rechaza_fecha_futura(usuario_administrador, cliente):
    futura = (timezone.localtime() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
    formulario = ComunicacionManualForm(_datos(cliente.pk, fecha_hora=futura), usuario=usuario_administrador)
    assert not formulario.is_valid()
    assert "futura" in str(formulario.errors["fecha_hora"])


def test_filtro_ofrece_canales_y_tipos(usuario_administrador):
    formulario = FiltroComunicacionesForm(usuario=usuario_administrador)
    canales = [valor for valor, _ in formulario.fields["canal"].choices]
    assert canales[0] == "" and "Reunión presencial" in canales
    tipos = [valor for valor, _ in formulario.fields["tipo"].choices]
    assert tipos == ["", Comunicacion.AUTOMATICA, Comunicacion.MANUAL]
