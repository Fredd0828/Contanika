"""Pruebas de las consultas del módulo 2: visibilidad por rol y filtros."""

from datetime import date

import pytest

from aplicaciones.calendario.models import (
    AnotacionCalendario,
    AnotacionCalendarioDestinatario,
    Vencimiento,
)
from aplicaciones.calendario.selectores import (
    anotaciones_visibles,
    filtrar_vencimientos,
    opciones_filtro_calendario,
    vencimientos_visibles,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def vencimiento_admin(cliente):
    return Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="IVA bimestral",
        ambito=Vencimiento.NACIONAL,
        fecha_vencimiento=date(2026, 3, 17),
    )


@pytest.fixture
def vencimiento_junior(cliente_junior):
    return Vencimiento.objects.create(
        cliente=cliente_junior,
        tipo_obligacion="Retención en la fuente",
        ambito=Vencimiento.MUNICIPAL,
        municipio="Chía",
        fecha_vencimiento=date(2026, 4, 20),
    )


# ---------------------------------------------------------------------------
# Visibilidad por rol
# ---------------------------------------------------------------------------


def test_administrador_ve_todos_los_vencimientos(
    usuario_administrador, vencimiento_admin, vencimiento_junior
):
    assert vencimientos_visibles(usuario_administrador).count() == 2


def test_junior_solo_ve_vencimientos_de_sus_clientes(usuario_junior, vencimiento_admin, vencimiento_junior):
    visibles = vencimientos_visibles(usuario_junior)
    assert visibles.count() == 1
    assert visibles.first() == vencimiento_junior


# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------


def test_filtrar_por_rango_de_fechas(usuario_administrador, vencimiento_admin, vencimiento_junior):
    resultado = filtrar_vencimientos(
        usuario_administrador, fecha_inicio=date(2026, 3, 1), fecha_fin=date(2026, 3, 31)
    )
    assert list(resultado) == [vencimiento_admin]


def test_filtrar_por_ambito(usuario_administrador, vencimiento_admin, vencimiento_junior):
    resultado = filtrar_vencimientos(usuario_administrador, ambito=Vencimiento.MUNICIPAL)
    assert list(resultado) == [vencimiento_junior]


def test_filtrar_por_tipo_obligacion(usuario_administrador, vencimiento_admin, vencimiento_junior):
    resultado = filtrar_vencimientos(usuario_administrador, tipo_obligacion="IVA bimestral")
    assert list(resultado) == [vencimiento_admin]


def test_filtrar_respeta_visibilidad_junior(usuario_junior, vencimiento_admin, vencimiento_junior):
    """Aunque el Junior filtre por un cliente ajeno, no obtiene resultados."""
    resultado = filtrar_vencimientos(usuario_junior, cliente=vencimiento_admin.cliente_id)
    assert resultado.count() == 0


# ---------------------------------------------------------------------------
# Anotaciones visibles
# ---------------------------------------------------------------------------


def test_anotacion_privada_solo_la_ve_el_autor(usuario_administrador, usuario_junior):
    anotacion = AnotacionCalendario.objects.create(
        fecha=date(2026, 10, 5),
        contenido="Privada",
        autor=usuario_administrador,
        visibilidad=AnotacionCalendario.PRIVADA,
    )
    assert anotacion in anotaciones_visibles(usuario_administrador)
    assert anotacion not in anotaciones_visibles(usuario_junior)


def test_anotacion_de_equipo_la_ven_todos(usuario_administrador, usuario_junior):
    anotacion = AnotacionCalendario.objects.create(
        fecha=date(2026, 10, 5),
        contenido="Para todos",
        autor=usuario_administrador,
        visibilidad=AnotacionCalendario.EQUIPO,
    )
    assert anotacion in anotaciones_visibles(usuario_junior)


def test_anotacion_por_rol(usuario_administrador, usuario_senior, usuario_junior):
    anotacion = AnotacionCalendario.objects.create(
        fecha=date(2026, 10, 5),
        contenido="Para seniors",
        autor=usuario_senior,
        visibilidad=AnotacionCalendario.POR_ROL,
    )
    assert anotacion in anotaciones_visibles(usuario_senior)
    assert anotacion not in anotaciones_visibles(usuario_junior)
    assert anotacion not in anotaciones_visibles(usuario_administrador)


def test_anotacion_por_etiqueta(usuario_administrador, usuario_senior, usuario_junior):
    anotacion = AnotacionCalendario.objects.create(
        fecha=date(2026, 10, 5),
        contenido="Etiquetado",
        autor=usuario_administrador,
        visibilidad=AnotacionCalendario.POR_ETIQUETA,
    )
    AnotacionCalendarioDestinatario.objects.create(anotacion_calendario=anotacion, usuario=usuario_junior)
    assert anotacion in anotaciones_visibles(usuario_junior)
    assert anotacion not in anotaciones_visibles(usuario_senior)


def test_opciones_filtro_combina_fuentes(cliente):
    """Las opciones de tipo de obligación combinan vencimientos y tabla DIAN."""
    Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="ICA municipal",
        fecha_vencimiento=date(2026, 5, 15),
    )
    opciones = opciones_filtro_calendario()
    assert "ICA municipal" in opciones["tipos_obligacion"]
    assert len(opciones["ambitos"]) == 3
