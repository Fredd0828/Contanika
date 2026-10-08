"""Pruebas del tablero del panel principal: cifras por sección, visibilidad por rol y módulos."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from aplicaciones.calendario.models import Vencimiento
from aplicaciones.finanzas.models import Abono, CuentaCobro
from aplicaciones.hallazgos.models import Hallazgo
from aplicaciones.seguridad import panel
from aplicaciones.seguridad.models import Modulo, PermisoRolModulo
from aplicaciones.tareas.models import Tarea

pytestmark = pytest.mark.django_db

# Miércoles: la semana en curso va del lunes 5 al domingo 11 de octubre.
HOY = date(2026, 10, 7)


def _vencimiento(cliente, fecha, estado=Vencimiento.PENDIENTE, tipo="IVA bimestral"):
    return Vencimiento.objects.create(
        cliente=cliente, tipo_obligacion=tipo, fecha_vencimiento=fecha, estado_presentacion=estado
    )


def _tarea(cliente, titulo, **campos):
    return Tarea.objects.create(cliente=cliente, titulo=titulo, **campos)


def _hallazgo(cliente, **campos):
    datos = {
        "tipo_hallazgo": "Conciliación bancaria",
        "fecha_inicio_periodo": date(2026, 9, 1),
        "fecha_fin_periodo": date(2026, 9, 30),
        "descripcion": "Diferencia en la conciliación.",
    }
    datos.update(campos)
    return Hallazgo.objects.create(cliente=cliente, **datos)


def _cuenta(cliente, valor, vence):
    return CuentaCobro.objects.create(cliente=cliente, valor_total=valor, fecha_vencimiento_pago=vence)


# ---------------------------------------------------------------------------
# Vencimientos
# ---------------------------------------------------------------------------


def test_vencimientos_cuenta_vencidos_proximos_y_cumplimiento(usuario_administrador, cliente):
    vencido = _vencimiento(cliente, HOY - timedelta(days=3))
    _vencimiento(cliente, HOY - timedelta(days=10), Vencimiento.PRESENTADA)
    _vencimiento(cliente, HOY, Vencimiento.EN_PROGRESO)
    _vencimiento(cliente, HOY + timedelta(days=7))
    _vencimiento(cliente, HOY + timedelta(days=8))
    _vencimiento(cliente, date(2026, 10, 2), Vencimiento.PRESENTADA)

    seccion = panel.seccion_vencimientos(usuario_administrador, HOY)

    assert seccion["vencidos"] == 1
    assert seccion["proximos"] == 2
    assert (seccion["presentados_mes"], seccion["del_mes"]) == (1, 5)
    assert seccion["cumplimiento_mes"] == 20
    # El vencido encabeza la lista y después siguen los próximos en orden de fecha.
    assert seccion["lista"][0]["vencimiento"] == vencido
    assert seccion["lista"][0]["dias_atraso"] == 3
    assert [item["dias"] for item in seccion["lista"]] == [-3, 0, 7, 8]


def test_vencimientos_se_agrupan_por_semana(usuario_administrador, cliente):
    _vencimiento(cliente, date(2026, 10, 4))  # domingo anterior: fuera del gráfico
    _vencimiento(cliente, date(2026, 10, 5))
    _vencimiento(cliente, date(2026, 10, 11), Vencimiento.PRESENTADA)
    _vencimiento(cliente, date(2026, 10, 12))
    _vencimiento(cliente, date(2026, 11, 29))  # último día de la octava semana
    _vencimiento(cliente, date(2026, 11, 30))  # novena semana: fuera del gráfico

    seccion = panel.seccion_vencimientos(usuario_administrador, HOY)
    por_presentar, presentados = (serie["valores"] for serie in seccion["grafico"]["series"])

    assert len(seccion["semanas"]) == panel.SEMANAS_GRAFICO
    assert seccion["semanas"][0]["inicio"] == date(2026, 10, 5)
    assert por_presentar == [1, 1, 0, 0, 0, 0, 0, 1]
    assert presentados == [1, 0, 0, 0, 0, 0, 0, 0]
    assert seccion["hay_semanas"]


def test_vencimientos_sin_datos(usuario_administrador):
    seccion = panel.seccion_vencimientos(usuario_administrador, HOY)
    assert seccion["cumplimiento_mes"] is None
    assert not seccion["hay_semanas"]
    assert seccion["lista"] == []


# ---------------------------------------------------------------------------
# Tareas
# ---------------------------------------------------------------------------


def test_tareas_por_estado_atrasadas_y_lista_propia(usuario_administrador, usuario_senior, cliente):
    ayer = HOY - timedelta(days=1)
    propia = _tarea(cliente, "Renta", responsable=usuario_administrador, fecha_vencimiento=ayer)
    _tarea(cliente, "Nómina", responsable=usuario_senior, estado=Tarea.EN_PROGRESO)
    _tarea(cliente, "Cierre contable", responsable=usuario_senior, estado=Tarea.TERMINADO)

    seccion = panel.seccion_tareas(usuario_administrador, HOY)

    assert {fila["estado"]: fila["cantidad"] for fila in seccion["por_estado"]} == {
        Tarea.POR_HACER: 1,
        Tarea.EN_PROGRESO: 1,
        Tarea.EN_REVISION: 0,
        Tarea.TERMINADO: 1,
    }
    assert (seccion["total"], seccion["activas"], seccion["atrasadas"]) == (3, 2, 1)
    assert seccion["avance"] == 33
    assert seccion["lista_propia"]
    assert [item["tarea"] for item in seccion["lista"]] == [propia]
    assert seccion["lista"][0]["atrasada"]


def test_tareas_sin_propias_muestra_las_del_equipo(usuario_administrador, usuario_senior, cliente):
    _tarea(cliente, "Sin fecha", responsable=usuario_senior)
    con_fecha = _tarea(cliente, "Con fecha", responsable=usuario_senior, fecha_vencimiento=HOY)

    seccion = panel.seccion_tareas(usuario_administrador, HOY)

    assert not seccion["lista_propia"]
    # Primero las que tienen fecha; las que no la tienen van al final.
    assert seccion["lista"][0]["tarea"] == con_fecha
    assert len(seccion["lista"]) == 2


def test_junior_cuenta_todas_las_tareas_del_equipo(usuario_junior, usuario_senior, cliente, cliente_junior):
    _tarea(cliente, "De otro cliente", responsable=usuario_senior)
    _tarea(cliente_junior, "De su cliente", responsable=usuario_senior)

    assert panel.seccion_tareas(usuario_junior, HOY)["total"] == 2


# ---------------------------------------------------------------------------
# Finanzas
# ---------------------------------------------------------------------------


def test_finanzas_saldo_mora_y_mes_en_curso(usuario_administrador, cliente):
    hoy = timezone.localdate()
    en_mora = _cuenta(cliente, Decimal("1000000"), hoy - timedelta(days=1))
    _cuenta(cliente, Decimal("500000"), hoy + timedelta(days=10))
    # Saldos provisionales: los fija el disparador de la base de datos.
    Abono.objects.create(
        cuenta_cobro=en_mora,
        fecha=hoy,
        monto=Decimal("400000"),
        responsable=usuario_administrador,
        saldo_anterior=Decimal("0"),
        saldo_resultante=Decimal("0"),
    )

    seccion = panel.seccion_finanzas(usuario_administrador, hoy)

    assert seccion["consolidado"]
    assert seccion["saldo"] == Decimal("1100000")
    assert seccion["en_mora"] == Decimal("600000")
    assert seccion["facturado_mes"] == Decimal("1500000")
    assert seccion["cobrado_mes"] == Decimal("400000")
    assert seccion["recaudo"] == 27
    assert len(seccion["meses"]) == panel.MESES_GRAFICO
    facturado, cobrado = (serie["valores"] for serie in seccion["grafico"]["series"])
    assert (facturado[-1], cobrado[-1]) == (1500000.0, 400000.0)
    assert [fila["cliente"] for fila in seccion["deudores"]] == [cliente]


def test_finanzas_del_junior_solo_sus_clientes(usuario_junior, cliente, cliente_junior):
    hoy = timezone.localdate()
    _cuenta(cliente, Decimal("1000000"), hoy + timedelta(days=10))
    _cuenta(cliente_junior, Decimal("300000"), hoy + timedelta(days=10))

    seccion = panel.seccion_finanzas(usuario_junior, hoy)

    assert not seccion["consolidado"]
    assert seccion["saldo"] == Decimal("300000")
    assert seccion["en_mora"] == Decimal("0")
    assert [fila["cliente"] for fila in seccion["deudores"]] == [cliente_junior]


def test_finanzas_sin_datos(usuario_administrador):
    seccion = panel.seccion_finanzas(usuario_administrador, HOY)
    assert seccion["recaudo"] is None
    assert not seccion["hay_meses"]
    assert [mes["etiqueta"] for mes in seccion["meses"]] == [
        "may 26",
        "jun 26",
        "jul 26",
        "ago 26",
        "sep 26",
        "oct 26",
    ]


# ---------------------------------------------------------------------------
# Hallazgos, clientes y equipo
# ---------------------------------------------------------------------------


def test_hallazgos_sin_cerrar_por_estado_y_prioridad(usuario_administrador, cliente):
    _hallazgo(cliente, estado=Hallazgo.EN_PROCESO, prioridad=Hallazgo.BAJA)
    alta = _hallazgo(cliente, estado=Hallazgo.ABIERTO, prioridad=Hallazgo.ALTA)
    _hallazgo(cliente, estado=Hallazgo.CERRADO, prioridad=Hallazgo.ALTA)

    seccion = panel.seccion_hallazgos(usuario_administrador)

    assert (seccion["abiertos"], seccion["alta"]) == (2, 1)
    assert {fila["estado"]: fila["cantidad"] for fila in seccion["por_estado"]} == {
        Hallazgo.ABIERTO: 1,
        Hallazgo.EN_PROCESO: 1,
        Hallazgo.PENDIENTE_CLIENTE: 0,
    }
    assert seccion["lista"][0] == alta
    assert len(seccion["lista"]) == 2


def test_clientes_activos_y_nuevos_del_mes(usuario_administrador, cliente, cliente_natural):
    cliente.fecha_registro = date(2026, 3, 1)
    cliente.save()
    cliente_natural.fecha_registro = HOY
    cliente_natural.estado = cliente_natural.INACTIVO
    cliente_natural.save()

    assert panel.seccion_clientes(HOY) == {"activos": 1, "nuevos_mes": 1}


def test_carga_del_equipo_solo_admin_y_senior(usuario_administrador, usuario_senior, usuario_junior):
    assert panel.armar_tablero(usuario_administrador, HOY)["equipo"] is not None
    assert panel.armar_tablero(usuario_senior, HOY)["equipo"] is not None
    assert panel.armar_tablero(usuario_junior, HOY)["equipo"] is None


# ---------------------------------------------------------------------------
# Tablero completo y vista
# ---------------------------------------------------------------------------


def test_modulo_inhabilitado_no_arma_su_seccion(usuario_junior, modulo_finanzas):
    PermisoRolModulo.objects.create(rol=usuario_junior.rol, modulo=modulo_finanzas, habilitado=False)

    tablero = panel.armar_tablero(usuario_junior, HOY)

    assert tablero["finanzas"] is None
    assert tablero["tareas"] is not None
    assert "Cartera por cobrar" not in [indicador["etiqueta"] for indicador in tablero["indicadores"]]


def test_indicadores_enlazan_a_su_modulo(usuario_administrador, cliente):
    _vencimiento(cliente, HOY - timedelta(days=1))

    indicadores = {i["etiqueta"]: i for i in panel.armar_tablero(usuario_administrador, HOY)["indicadores"]}

    assert indicadores["Vencidos sin presentar"]["valor"] == 1
    assert indicadores["Vencidos sin presentar"]["tono"] == "rojo"
    assert indicadores["Vencidos sin presentar"]["url"] == reverse("calendario:lista")
    assert indicadores["Cartera por cobrar"]["valor"] == "$ 0"
    assert indicadores["Clientes activos"]["valor"] == 1


def test_panel_muestra_el_tablero_y_ya_no_los_modulos(client, usuario_administrador, cliente):
    hoy = timezone.localdate()
    _vencimiento(cliente, hoy)
    _cuenta(cliente, Decimal("800000"), hoy + timedelta(days=5))
    client.force_login(usuario_administrador)

    respuesta = client.get(reverse("seguridad:panel"))
    contenido = respuesta.content.decode()

    assert respuesta.status_code == 200
    assert "modulos" not in respuesta.context
    assert "Módulos del sistema" not in contenido
    for texto in ("Vencimientos", "Tareas", "Finanzas", "Hallazgos", "Carga del equipo"):
        assert texto in contenido
    assert 'id="graficoVencimientos"' in contenido
    assert 'id="graficoFinanzas"' in contenido
    assert "$ 800.000" in contenido


def test_panel_sin_datos_muestra_estados_vacios(client, usuario_senior):
    client.force_login(usuario_senior)

    contenido = client.get(reverse("seguridad:panel")).content.decode()

    assert "No hay vencimientos registrados" in contenido
    assert "Todavía no hay tareas en el tablero" in contenido
    assert "<canvas" not in contenido


def test_panel_sin_modulos_habilitados(client, usuario_senior):
    for codigo, nombre in Modulo.OPCIONES_CODIGO:
        if codigo != Modulo.SEC_PANEL:
            _inhabilitar(usuario_senior.rol, codigo, nombre)
    client.force_login(usuario_senior)

    contenido = client.get(reverse("seguridad:panel")).content.decode()

    assert "Su rol no tiene módulos habilitados" in contenido


# ---------------------------------------------------------------------------
# Panel, menú y pestañas según lo que el Administrador habilite por rol
# ---------------------------------------------------------------------------


def _inhabilitar(rol, codigo, nombre="Módulo"):
    modulo, _ = Modulo.objects.get_or_create(codigo_modulo=codigo, defaults={"nombre_modulo": nombre})
    PermisoRolModulo.objects.update_or_create(rol=rol, modulo=modulo, defaults={"habilitado": False})


def _releer(usuario):
    """Los módulos habilitados se guardan en caché por instancia: se vuelve a leer el usuario."""
    return type(usuario).objects.get(pk=usuario.pk)


@pytest.mark.parametrize("nombre_usuario", ["usuario_junior", "usuario_senior", "usuario_administrador"])
def test_por_defecto_todos_los_roles_ven_el_panel(client, request, nombre_usuario):
    client.force_login(request.getfixturevalue(nombre_usuario))
    respuesta = client.get(reverse("seguridad:panel"))
    assert respuesta.status_code == 200
    etiquetas = [
        item["etiqueta"] for seccion in respuesta.context["menu_lateral"] for item in seccion["items"]
    ]
    assert "Panel" in etiquetas


@pytest.mark.parametrize("nombre_usuario", ["usuario_junior", "usuario_senior"])
def test_rol_sin_panel_empieza_en_el_calendario(client, request, nombre_usuario):
    usuario = request.getfixturevalue(nombre_usuario)
    _inhabilitar(usuario.rol, Modulo.SEC_PANEL)
    client.force_login(usuario)

    respuesta = client.get(reverse("seguridad:panel"))

    assert respuesta.status_code == 302
    assert respuesta.url == reverse("calendario:calendario")
    menu = client.get(reverse("seguridad:ayuda")).context["menu_lateral"]
    etiquetas = [item["etiqueta"] for seccion in menu for item in seccion["items"]]
    assert "Panel" not in etiquetas and "Calendario" in etiquetas


def test_rol_sin_panel_ni_calendario_empieza_en_tareas_y_sin_modulos_en_la_ayuda(client, usuario_junior):
    _inhabilitar(usuario_junior.rol, Modulo.SEC_PANEL)
    _inhabilitar(usuario_junior.rol, Modulo.MOD02_CALENDARIO)
    client.force_login(usuario_junior)
    assert client.get(reverse("seguridad:panel")).url == reverse("tareas:tablero")

    for codigo, nombre in Modulo.OPCIONES_CODIGO:
        _inhabilitar(usuario_junior.rol, codigo, nombre)
    client.force_login(_releer(usuario_junior))
    assert client.get(reverse("seguridad:panel")).url == reverse("seguridad:ayuda")


def test_el_administrador_habilita_y_quita_el_panel_desde_la_matriz(
    client, usuario_administrador, usuario_junior
):
    panel_principal = Modulo.objects.create(codigo_modulo=Modulo.SEC_PANEL, nombre_modulo="Panel principal")
    client.force_login(usuario_administrador)
    contenido = client.get(reverse("seguridad:permisos")).content.decode()
    assert "Panel principal" in contenido and reverse("reportes:visibilidad") in contenido

    # Se guarda la matriz con el panel marcado solo para el Administrador.
    client.post(
        reverse("seguridad:permisos"), {f"permiso_{usuario_administrador.rol.pk}_{panel_principal.pk}": "on"}
    )
    client.force_login(usuario_junior)
    assert client.get(reverse("seguridad:panel")).status_code == 302

    client.force_login(usuario_administrador)
    client.post(
        reverse("seguridad:permisos"),
        {
            f"permiso_{usuario_administrador.rol.pk}_{panel_principal.pk}": "on",
            f"permiso_{usuario_junior.rol.pk}_{panel_principal.pk}": "on",
        },
    )
    client.force_login(_releer(usuario_junior))
    assert client.get(reverse("seguridad:panel")).status_code == 200


def test_la_ayuda_esta_en_el_menu_lateral_de_todos(client, usuario_junior, usuario_administrador):
    for usuario in (usuario_junior, usuario_administrador):
        client.force_login(usuario)
        menu = client.get(reverse("seguridad:ayuda")).context["menu_lateral"]
        ayuda = [item for seccion in menu for item in seccion["items"] if item["etiqueta"] == "Ayuda"]
        assert ayuda and ayuda[0]["url"] == reverse("seguridad:ayuda") and ayuda[0]["activo"]


@pytest.mark.parametrize(
    ("pestana", "codigo", "dato"),
    [
        ("vencimientos", Modulo.MOD02_CALENDARIO, "vencimientos"),
        ("documentos", Modulo.MOD04_DOCUMENTOS, "documentos"),
        ("hallazgos", Modulo.MOD05_HALLAZGOS, "hallazgos"),
        ("honorarios", Modulo.MOD06_FINANZAS, "cuentas_cobro"),
        ("expediente", Modulo.MOD09_EXPEDIENTE, "anotaciones"),
        ("comunicaciones", Modulo.MOD07_COMUNICACIONES, "comunicaciones"),
    ],
)
def test_ficha_del_cliente_oculta_la_pestana_del_modulo_inhabilitado(
    client, usuario_senior, cliente, pestana, codigo, dato
):
    url = reverse("clientes:detalle", args=[cliente.pk])
    client.force_login(usuario_senior)
    respuesta = client.get(url)
    assert f'id="tab-{pestana}"' in respuesta.content.decode() and dato in respuesta.context

    _inhabilitar(usuario_senior.rol, codigo)
    client.force_login(_releer(usuario_senior))
    respuesta = client.get(url)
    contenido = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert f'id="tab-{pestana}' not in contenido
    assert dato not in respuesta.context
    # Las demás pestañas siguen ahí.
    assert contenido.count('class="tab-pane') >= 6


def test_datos_iniciales_dejan_al_junior_sin_panel_honorarios_ni_reportes_financieros(db):
    from django.core.management import call_command

    from aplicaciones.reportes.models import PermisoReporteRol, Reporte
    from aplicaciones.seguridad.models import Rol

    call_command("cargar_datos_iniciales", verbosity=0)

    def modulos_inhabilitados(nombre_rol):
        permisos = PermisoRolModulo.objects.filter(rol__nombre_rol=nombre_rol, habilitado=False)
        return set(permisos.values_list("modulo__codigo_modulo", flat=True))

    def reportes_inhabilitados(nombre_rol):
        permisos = PermisoReporteRol.objects.filter(rol__nombre_rol=nombre_rol, habilitado=False)
        return set(permisos.values_list("reporte__nombre_reporte", flat=True))

    assert modulos_inhabilitados(Rol.CONTADOR_JUNIOR) == {Modulo.MOD06_FINANZAS, Modulo.SEC_PANEL}
    assert reportes_inhabilitados(Rol.CONTADOR_JUNIOR) == {
        Reporte.CARTERA,
        Reporte.CUENTAS_COBRO,
        Reporte.INGRESOS,
    }
    assert not modulos_inhabilitados(Rol.CONTADOR_SENIOR) and not reportes_inhabilitados(Rol.CONTADOR_SENIOR)

    # El comando no pisa lo que el Administrador cambie después.
    PermisoRolModulo.objects.filter(rol__nombre_rol=Rol.CONTADOR_JUNIOR).update(habilitado=True)
    call_command("cargar_datos_iniciales", verbosity=0)
    assert not modulos_inhabilitados(Rol.CONTADOR_JUNIOR)
