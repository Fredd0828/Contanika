"""Pruebas de las consultas del módulo 2: visibilidad por rol y filtros."""

from datetime import date, timedelta

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
    vencimientos_proximos,
    vencimientos_vencidos,
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


def test_opciones_filtro_incluye_catalogo_de_obligaciones(cliente):
    """Una obligación del catálogo (Módulo 1) se sugiere aunque no tenga vencimientos ni tabla DIAN."""
    from aplicaciones.clientes.models import ObligacionTributaria

    ObligacionTributaria.objects.get_or_create(
        nombre="Exógena nacional", defaults={"ambito": ObligacionTributaria.NACIONAL}
    )
    opciones = opciones_filtro_calendario()
    assert "Exógena nacional" in opciones["tipos_obligacion"]


# ---------------------------------------------------------------------------
# Próximos y vencidos
# ---------------------------------------------------------------------------


def test_vencimientos_proximos_incluye_hoy_y_futuros(usuario_administrador, cliente):
    hoy = date.today()
    pasado = Vencimiento.objects.create(
        cliente=cliente, tipo_obligacion="IVA bimestral", fecha_vencimiento=hoy - timedelta(days=1)
    )
    de_hoy = Vencimiento.objects.create(
        cliente=cliente, tipo_obligacion="IVA bimestral", fecha_vencimiento=hoy
    )
    futuro = Vencimiento.objects.create(
        cliente=cliente, tipo_obligacion="IVA bimestral", fecha_vencimiento=hoy + timedelta(days=5)
    )

    resultado = list(vencimientos_proximos(usuario_administrador))

    assert pasado not in resultado
    assert resultado == [de_hoy, futuro]


def test_vencimientos_vencidos_excluye_presentados(usuario_administrador, cliente):
    hoy = date.today()
    pendiente = Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="IVA bimestral",
        fecha_vencimiento=hoy - timedelta(days=3),
        estado_presentacion=Vencimiento.PENDIENTE,
    )
    Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion="Retención en la fuente",
        fecha_vencimiento=hoy - timedelta(days=2),
        estado_presentacion=Vencimiento.PRESENTADA,
    )
    Vencimiento.objects.create(cliente=cliente, tipo_obligacion="IVA bimestral", fecha_vencimiento=hoy)

    resultado = list(vencimientos_vencidos(usuario_administrador))

    assert resultado == [pendiente]


def test_vencimientos_proximos_limita_a_diez(usuario_administrador, cliente):
    hoy = date.today()
    for i in range(12):
        Vencimiento.objects.create(
            cliente=cliente, tipo_obligacion="IVA bimestral", fecha_vencimiento=hoy + timedelta(days=i)
        )

    assert len(list(vencimientos_proximos(usuario_administrador))) == 10


def test_vencimientos_proximos_respeta_visibilidad_junior(usuario_junior, cliente, cliente_junior):
    hoy = date.today()
    Vencimiento.objects.create(cliente=cliente, tipo_obligacion="IVA bimestral", fecha_vencimiento=hoy)
    del_junior = Vencimiento.objects.create(
        cliente=cliente_junior, tipo_obligacion="IVA bimestral", fecha_vencimiento=hoy
    )

    assert list(vencimientos_proximos(usuario_junior)) == [del_junior]
