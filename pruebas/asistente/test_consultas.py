"""Pruebas del catálogo de consultas del asistente: resultados, visibilidad y protección de clientes."""

from datetime import timedelta

import pytest

from aplicaciones.asistente import consultas
from aplicaciones.calendario.models import Vencimiento
from aplicaciones.clientes.models import Cliente
from aplicaciones.hallazgos.models import Hallazgo
from aplicaciones.seguridad.models import Modulo
from aplicaciones.tareas.models import Tarea

from .conftest import HOY, abonar, crear_cuenta, crear_hallazgo, crear_tarea, crear_vencimiento, inhabilitar

pytestmark = pytest.mark.django_db


def _ejecutar(usuario, slug, cliente_id=None):
    return consultas.ejecutar(usuario, consultas.POR_SLUG[slug], cliente_id, hoy=HOY)


# ---------------------------------------------------------------------------
# Catálogo y visibilidad
# ---------------------------------------------------------------------------


def test_el_catalogo_esta_completo():
    assert len(consultas.POR_SLUG) == len(consultas.CONSULTAS)
    codigos = {codigo for codigo, _ in Modulo.OPCIONES_CODIGO}
    for consulta in consultas.CONSULTAS:
        assert consulta.pregunta.endswith("?") and consulta.descripcion
        assert consulta.icono.startswith("bi-")
        assert consulta.modulo in codigos
        assert (consulta.clientes is not None) == consulta.pide_cliente


def test_el_administrador_ve_todas_las_consultas(usuario_administrador):
    assert consultas.consultas_visibles(usuario_administrador) == list(consultas.CONSULTAS)


def test_un_modulo_inhabilitado_oculta_sus_consultas(usuario_junior, rol_junior):
    inhabilitar(rol_junior, Modulo.MOD06_FINANZAS)

    visibles = {consulta.slug for consulta in consultas.consultas_visibles(usuario_junior)}

    assert "cartera-pendiente" not in visibles and "saldo-cliente" not in visibles
    assert "vencimientos-semana" in visibles
    assert consultas.obtener_visible(usuario_junior, "cartera-pendiente") is None
    assert consultas.obtener_visible(usuario_junior, "vencimientos-semana") is not None
    assert consultas.obtener_visible(usuario_junior, "no-existe") is None


def test_las_opciones_de_cliente_respetan_cada_pregunta(usuario_senior, cliente):
    # El Senior ve el calendario de todos los clientes, pero la cartera solo de los suyos.
    assert consultas.POR_SLUG["vencimientos-cliente"].opciones_cliente(usuario_senior) == [
        (cliente.pk, "Comercializadora La Rebaja SAS · 900123456")
    ]
    assert consultas.POR_SLUG["saldo-cliente"].opciones_cliente(usuario_senior) == []
    assert consultas.POR_SLUG["vencimientos-semana"].opciones_cliente(usuario_senior) == []


# ---------------------------------------------------------------------------
# Calendario
# ---------------------------------------------------------------------------


def test_vencimientos_de_la_semana(usuario_administrador, cliente):
    crear_vencimiento(cliente, HOY, tipo="Retención en la fuente", responsable=usuario_administrador)
    crear_vencimiento(cliente, HOY + timedelta(days=6), Vencimiento.EN_PROGRESO)
    crear_vencimiento(cliente, HOY + timedelta(days=2), Vencimiento.PRESENTADA)
    crear_vencimiento(cliente, HOY + timedelta(days=7))
    crear_vencimiento(cliente, HOY - timedelta(days=1))

    respuesta = _ejecutar(usuario_administrador, "vencimientos-semana")

    assert respuesta.total == 2
    assert respuesta.titulo == "Vencimientos sin presentar del 16/11/2026 al 22/11/2026: 2"
    assert respuesta.filas[0] == (
        "16/11/2026",
        "Comercializadora La Rebaja SAS",
        "Retención en la fuente",
        "Pendiente",
        "Paula Andrea Blanco",
    )
    assert respuesta.filas[1][3] == "En progreso" and respuesta.filas[1][4] == "Sin asignar"
    assert respuesta.url == "/calendario/vencimientos/"


def test_vencimientos_atrasados(usuario_administrador, cliente):
    crear_vencimiento(cliente, HOY - timedelta(days=5))
    crear_vencimiento(cliente, HOY - timedelta(days=9), Vencimiento.PRESENTADA)
    crear_vencimiento(cliente, HOY)

    respuesta = _ejecutar(usuario_administrador, "vencimientos-atrasados")

    assert respuesta.total == 1
    assert respuesta.filas[0][3] == "Pendiente · vencido"
    assert "Presentada" in respuesta.nota


def test_sin_vencimientos_atrasados_no_hay_nota(usuario_administrador):
    respuesta = _ejecutar(usuario_administrador, "vencimientos-atrasados")

    assert respuesta.total == 0 and respuesta.filas == [] and respuesta.nota == ""
    assert respuesta.vacio.startswith("No hay vencimientos atrasados")


def test_vencimientos_de_un_cliente(usuario_administrador, cliente, cliente_natural):
    crear_vencimiento(cliente, HOY - timedelta(days=3))
    crear_vencimiento(cliente, HOY + timedelta(days=30))
    crear_vencimiento(cliente, HOY + timedelta(days=40), Vencimiento.PRESENTADA)
    crear_vencimiento(cliente_natural, HOY)

    respuesta = _ejecutar(usuario_administrador, "vencimientos-cliente", cliente.pk)

    assert respuesta.total == 2
    assert respuesta.columnas == ("Fecha", "Obligación", "Estado", "Responsable")
    assert [fila[0] for fila in respuesta.filas] == ["13/11/2026", "16/12/2026"]
    assert respuesta.url == f"/clientes/{cliente.pk}/"


@pytest.mark.parametrize("cliente_id", [None, "", "abc", 999999])
def test_una_pregunta_por_cliente_exige_un_cliente_valido(usuario_administrador, cliente_id):
    with pytest.raises(consultas.ClienteNoPermitido):
        _ejecutar(usuario_administrador, "vencimientos-cliente", cliente_id)


def test_un_cliente_inactivo_no_se_puede_consultar(usuario_administrador, cliente):
    cliente.estado = Cliente.INACTIVO
    cliente.save()

    with pytest.raises(consultas.ClienteNoPermitido):
        _ejecutar(usuario_administrador, "vencimientos-cliente", cliente.pk)


def test_la_respuesta_se_recorta_y_avisa_cuantas_faltan(usuario_administrador, cliente):
    for dias in range(consultas.LIMITE_FILAS + 2):
        crear_vencimiento(cliente, HOY - timedelta(days=dias + 1))

    respuesta = _ejecutar(usuario_administrador, "vencimientos-atrasados")

    assert respuesta.total == consultas.LIMITE_FILAS + 2
    assert len(respuesta.filas) == consultas.LIMITE_FILAS
    assert respuesta.omitidas == 2


# ---------------------------------------------------------------------------
# Tareas y hallazgos
# ---------------------------------------------------------------------------


def test_mis_tareas_solo_trae_las_propias_sin_terminar(usuario_senior, usuario_administrador, cliente):
    crear_tarea(
        cliente, "Conciliar bancos", responsable=usuario_senior, fecha_vencimiento=HOY - timedelta(days=1)
    )
    crear_tarea(cliente, "Revisar nómina", responsable=usuario_senior)
    crear_tarea(cliente, "Cerrar mes", responsable=usuario_senior, estado=Tarea.TERMINADO)
    crear_tarea(cliente, "Tarea de otro", responsable=usuario_administrador)

    respuesta = _ejecutar(usuario_senior, "mis-tareas")

    assert respuesta.total == 2
    assert respuesta.filas[0][0] == "Conciliar bancos"
    assert respuesta.filas[0][4] == "15/11/2026 · atrasada"
    assert respuesta.filas[1][4] == "Sin fecha"


def test_tareas_atrasadas_del_equipo(usuario_junior, usuario_administrador, cliente):
    crear_tarea(
        cliente, "Atrasada", responsable=usuario_administrador, fecha_vencimiento=HOY - timedelta(days=2)
    )
    crear_tarea(cliente, "Terminada", fecha_vencimiento=HOY - timedelta(days=2), estado=Tarea.TERMINADO)
    crear_tarea(cliente, "A tiempo", fecha_vencimiento=HOY)

    respuesta = _ejecutar(usuario_junior, "tareas-atrasadas")

    assert respuesta.total == 1
    assert respuesta.filas[0] == (
        "Atrasada",
        "Comercializadora La Rebaja SAS",
        "Paula Andrea Blanco",
        "Por hacer",
        "14/11/2026 · atrasada",
    )


def test_hallazgos_sin_cerrar(usuario_junior, cliente):
    crear_hallazgo(cliente, estado=Hallazgo.EN_PROCESO, prioridad=Hallazgo.ALTA)
    crear_hallazgo(cliente, estado=Hallazgo.CERRADO)

    respuesta = _ejecutar(usuario_junior, "hallazgos-abiertos")

    assert respuesta.total == 1
    assert respuesta.filas[0][1:4] == ("Conciliación bancaria", "Alta", "En proceso")


# ---------------------------------------------------------------------------
# Finanzas
# ---------------------------------------------------------------------------


def test_cartera_pendiente_del_administrador(usuario_administrador, cliente):
    cuenta = crear_cuenta(cliente, "1000000", HOY - timedelta(days=10))
    abonar(cuenta, "400000", usuario_administrador)
    crear_cuenta(cliente, "250000", HOY + timedelta(days=5))

    respuesta = _ejecutar(usuario_administrador, "cartera-pendiente")

    assert respuesta.total == 1
    assert respuesta.filas[0] == ("Comercializadora La Rebaja SAS", "$ 850.000", "2", "10 días")
    assert respuesta.nota == "Saldo total pendiente: $ 850.000."


def test_la_cartera_del_senior_se_limita_a_sus_clientes(usuario_senior, cliente):
    crear_cuenta(cliente, "500000", HOY)  # cliente asignado a la Administradora

    respuesta = _ejecutar(usuario_senior, "cartera-pendiente")

    assert respuesta.total == 0 and respuesta.nota == ""


def test_saldo_de_un_cliente(usuario_administrador, cliente):
    al_dia = crear_cuenta(cliente, "300000", HOY + timedelta(days=5))
    en_mora = crear_cuenta(cliente, "700000", HOY - timedelta(days=3))
    pagada = crear_cuenta(cliente, "200000", HOY - timedelta(days=30))
    abonar(pagada, "200000", usuario_administrador)
    abonar(en_mora, "100000", usuario_administrador)

    respuesta = _ejecutar(usuario_administrador, "saldo-cliente", cliente.pk)

    assert respuesta.titulo == "Saldo pendiente de Comercializadora La Rebaja SAS: $ 900.000"
    assert respuesta.filas == [
        (f"N.º {en_mora.pk}", "$ 700.000", "$ 600.000", "13/11/2026 · en mora"),
        (f"N.º {al_dia.pk}", "$ 300.000", "$ 300.000", "21/11/2026"),
    ]


def test_el_senior_no_consulta_el_saldo_de_un_cliente_ajeno(usuario_senior, cliente):
    crear_cuenta(cliente, "500000", HOY)

    with pytest.raises(consultas.ClienteNoPermitido):
        _ejecutar(usuario_senior, "saldo-cliente", cliente.pk)
