"""Pruebas de los selectores del módulo 5: hallazgos y revisiones contables."""

from datetime import date

import pytest

from aplicaciones.comunes.models import Adjunto
from aplicaciones.hallazgos import selectores
from aplicaciones.hallazgos.models import Hallazgo

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_root_temporal(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def hallazgo_cliente(cliente, usuario_administrador):
    return Hallazgo.objects.create(
        cliente=cliente,
        tipo_hallazgo="Inconsistencia",
        fecha_inicio_periodo=date(2026, 1, 1),
        fecha_fin_periodo=date(2026, 1, 31),
        responsable=usuario_administrador,
        descripcion="Diferencia detectada en la conciliación bancaria.",
    )


@pytest.fixture
def hallazgo_cliente_junior(cliente_junior, usuario_administrador):
    return Hallazgo.objects.create(
        cliente=cliente_junior,
        tipo_hallazgo="Observación",
        fecha_inicio_periodo=date(2026, 2, 1),
        fecha_fin_periodo=date(2026, 2, 28),
        responsable=usuario_administrador,
        descripcion="Falta soporte de un anticipo.",
    )


def test_hallazgos_visibles_junior_filtra_por_cliente_asignado(
    usuario_junior, hallazgo_cliente, hallazgo_cliente_junior
):
    visibles = selectores.hallazgos_visibles(usuario_junior)
    assert list(visibles) == [hallazgo_cliente_junior]


def test_hallazgos_visibles_admin_ve_todos(usuario_administrador, hallazgo_cliente, hallazgo_cliente_junior):
    visibles = selectores.hallazgos_visibles(usuario_administrador)
    assert set(visibles) == {hallazgo_cliente, hallazgo_cliente_junior}


def test_clientes_para_hallazgos_junior_solo_ve_los_propios(usuario_junior, cliente, cliente_junior):
    assert list(selectores.clientes_para_hallazgos(usuario_junior)) == [cliente_junior]


def test_filtrar_hallazgos_por_tipo_estado_responsable_y_rango(
    usuario_administrador, hallazgo_cliente, hallazgo_cliente_junior
):
    assert list(selectores.filtrar_hallazgos(usuario_administrador, tipo="Inconsistencia")) == [
        hallazgo_cliente
    ]
    assert set(selectores.filtrar_hallazgos(usuario_administrador, responsable=usuario_administrador)) == {
        hallazgo_cliente,
        hallazgo_cliente_junior,
    }
    hallazgo_cliente.estado = Hallazgo.CERRADO
    hallazgo_cliente.save(update_fields=["estado"])
    assert list(selectores.filtrar_hallazgos(usuario_administrador, estado=Hallazgo.CERRADO)) == [
        hallazgo_cliente
    ]
    assert list(selectores.filtrar_hallazgos(usuario_administrador, desde=date(2026, 2, 1))) == [
        hallazgo_cliente_junior
    ]
    assert list(selectores.filtrar_hallazgos(usuario_administrador, hasta=date(2026, 1, 31))) == [
        hallazgo_cliente
    ]


def test_filtrar_hallazgos_por_rango_busca_traslape_del_periodo(
    usuario_administrador, hallazgo_cliente, hallazgo_cliente_junior
):
    # El rango del 15 de enero al 10 de febrero cruza ambos períodos, aunque
    # ninguno de los dos empieza dentro del rango consultado.
    assert set(
        selectores.filtrar_hallazgos(usuario_administrador, desde=date(2026, 1, 15), hasta=date(2026, 2, 10))
    ) == {hallazgo_cliente, hallazgo_cliente_junior}
    semestre = Hallazgo.objects.create(
        cliente=hallazgo_cliente.cliente,
        tipo_hallazgo="Inconsistencia",
        fecha_inicio_periodo=date(2026, 1, 1),
        fecha_fin_periodo=date(2026, 6, 30),
        responsable=usuario_administrador,
        descripcion="Revisión semestral.",
    )
    assert list(
        selectores.filtrar_hallazgos(usuario_administrador, desde=date(2026, 3, 1), hasta=date(2026, 3, 31))
    ) == [semestre]


def test_opciones_filtro_hallazgos_devuelve_tipos_distintos(
    usuario_administrador, hallazgo_cliente, hallazgo_cliente_junior
):
    opciones = selectores.opciones_filtro_hallazgos(usuario_administrador)
    assert set(opciones["tipos_hallazgo"]) == {"Inconsistencia", "Observación"}


def test_adjuntos_del_hallazgo_no_mezcla_otro_origen(hallazgo_cliente):
    propio = Adjunto.objects.create(
        tabla_origen=Adjunto.HALLAZGO,
        id_origen=hallazgo_cliente.pk,
        archivo="adjuntos/hallazgos/prueba.pdf",
        nombre_archivo="soporte.pdf",
    )
    Adjunto.objects.create(
        tabla_origen=Adjunto.ANOTACION,
        id_origen=hallazgo_cliente.pk,
        archivo="adjuntos/hallazgos/otro.pdf",
        nombre_archivo="otro.pdf",
    )
    assert list(selectores.adjuntos_del_hallazgo(hallazgo_cliente)) == [propio]


def test_hallazgos_del_cliente_limita_al_cliente_indicado(
    usuario_administrador, cliente, hallazgo_cliente, hallazgo_cliente_junior
):
    assert list(selectores.hallazgos_del_cliente(usuario_administrador, cliente)) == [hallazgo_cliente]
