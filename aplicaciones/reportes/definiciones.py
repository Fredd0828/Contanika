"""
Definición de los seis reportes del módulo 10 (spec y HU028, HU029, HU048, HU051).

Cada definición indica su formulario de filtros y arma un `ResultadoReporte`
a partir de los filtros validados. Los reportes de clientes, vencimientos y
tareas traen la información de todo el despacho para cualquier rol, igual que
sus módulos (decisión del usuario, 7-oct-2026; modifica HU029-1 y HU051-4).
En los financieros (cartera y cuentas de cobro), Senior y Junior solo ven sus
clientes asignados; el de ingresos es siempre el total consolidado del
despacho (spec del Módulo 10).
"""

from collections import OrderedDict
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from aplicaciones.calendario.models import Vencimiento
from aplicaciones.clientes.models import Cliente
from aplicaciones.finanzas import selectores as selectores_finanzas
from aplicaciones.finanzas.models import Abono, CuentaCobro, Honorario
from aplicaciones.finanzas.templatetags.finanzas_tags import formato_pesos
from aplicaciones.tareas.models import Tarea

from . import formularios
from .models import Reporte
from .resultados import FECHA, NUMERO, PESOS, PORCENTAJE, Columna, Grafico, ResultadoReporte, Seccion

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def _restringir(usuario, consulta, campo_responsable):
    """Reportes financieros: Senior y Junior solo ven la información de sus clientes asignados."""
    if usuario.es_administrador:
        return consulta
    return consulta.filter(**{campo_responsable: usuario})


class DefinicionReporte:
    nombre = ""
    slug = ""
    icono = "bi-file-earmark-bar-graph"
    descripcion = ""
    formulario = formularios.FiltroBase

    def generar(self, usuario, filtros, hoy=None):
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 1. Clientes
# ---------------------------------------------------------------------------


class ReporteClientes(DefinicionReporte):
    nombre = Reporte.CLIENTES
    slug = "clientes"
    icono = "bi-people-fill"
    descripcion = "Datos fiscales, ubicación, servicios, contacto y responsable de cada cliente."
    formulario = formularios.FiltroClientesForm

    def generar(self, usuario, filtros, hoy=None):
        consulta = (
            Cliente.objects.select_related("responsable")
            .prefetch_related("servicios__tipo_servicio", "municipios_adicionales")
            .order_by("nombre_razon_social")
        )
        if filtros.get("desde"):
            consulta = consulta.filter(fecha_registro__gte=filtros["desde"])
        if filtros.get("hasta"):
            consulta = consulta.filter(fecha_registro__lte=filtros["hasta"])
        if filtros.get("responsable"):
            consulta = consulta.filter(responsable=filtros["responsable"])
        if filtros.get("regimen"):
            consulta = consulta.filter(regimen_tributario=filtros["regimen"])
        if filtros.get("ciudad"):
            consulta = consulta.filter(ciudad=filtros["ciudad"])
        if filtros.get("estado"):
            consulta = consulta.filter(estado=filtros["estado"])
        if filtros.get("servicio"):
            consulta = consulta.filter(servicios__tipo_servicio=filtros["servicio"]).distinct()

        columnas = [
            Columna("Nombre o razón social", ancho=30),
            Columna("Documento", ancho=14),
            Columna("Tipo de persona", ancho=12),
            Columna("Régimen", ancho=18),
            Columna("Resp. IVA", ancho=8),
            Columna("Ciudad / municipio", ancho=18),
            Columna("Municipios adicionales", ancho=20),
            Columna("Servicios", ancho=24),
            Columna("Contacto", ancho=22),
            Columna("Responsable", ancho=18),
            Columna("Estado", ancho=9),
            Columna("Registro", FECHA, ancho=11),
        ]
        filas = []
        for cliente in consulta:
            filas.append(
                [
                    cliente.nombre_razon_social,
                    f"{cliente.tipo_documento} {cliente.nit_cedula}",
                    cliente.tipo_persona,
                    cliente.regimen_tributario,
                    "Sí" if cliente.responsable_iva else "No",
                    cliente.municipio_principal or cliente.ciudad,
                    ", ".join(m.municipio for m in cliente.municipios_adicionales.all()),
                    ", ".join(s.tipo_servicio.nombre_servicio for s in cliente.servicios.all()),
                    " / ".join(filter(None, [cliente.informacion_contacto, cliente.correo_cliente])),
                    cliente.responsable.nombre if cliente.responsable else "",
                    cliente.estado,
                    cliente.fecha_registro,
                ]
            )
        activos = sum(1 for fila in filas if fila[10] == Cliente.ACTIVO)
        return ResultadoReporte(
            secciones=[Seccion("Clientes", columnas, filas)],
            resumen=[
                ("Clientes", str(len(filas))),
                ("Activos", str(activos)),
                ("Inactivos", str(len(filas) - activos)),
            ],
        )


# ---------------------------------------------------------------------------
# 2. Vencimientos tributarios
# ---------------------------------------------------------------------------


class ReporteVencimientos(DefinicionReporte):
    nombre = Reporte.VENCIMIENTOS
    slug = "vencimientos"
    icono = "bi-calendar2-check-fill"
    descripcion = "Obligaciones por cliente con fecha, estado de presentación y validación; vencidas en rojo."
    formulario = formularios.FiltroVencimientosForm

    def generar(self, usuario, filtros, hoy=None):
        hoy = hoy or timezone.localdate()
        consulta = Vencimiento.objects.select_related("cliente", "responsable").order_by(
            "fecha_vencimiento", "cliente__nombre_razon_social"
        )
        for campo, filtro in (
            ("desde", "fecha_vencimiento__gte"),
            ("hasta", "fecha_vencimiento__lte"),
            ("cliente", "cliente"),
            ("responsable", "responsable"),
            ("tipo_obligacion", "tipo_obligacion"),
            ("ambito", "ambito"),
            ("estado", "estado_presentacion"),
        ):
            if filtros.get(campo):
                consulta = consulta.filter(**{filtro: filtros[campo]})

        columnas = [
            Columna("Cliente", ancho=28),
            Columna("Tipo de obligación", ancho=24),
            Columna("Ámbito", ancho=10),
            Columna("Municipio", ancho=14),
            Columna("Período", ancho=9),
            Columna("Vence", FECHA, ancho=11),
            Columna("Estado", ancho=12),
            Columna("Validación DIAN", ancho=16),
            Columna("Responsable", ancho=18),
        ]
        filas, resaltadas = [], set()
        for indice, vencimiento in enumerate(consulta):
            filas.append(
                [
                    vencimiento.cliente.nombre_razon_social,
                    vencimiento.tipo_obligacion,
                    vencimiento.ambito,
                    vencimiento.municipio,
                    vencimiento.periodo_gravable,
                    vencimiento.fecha_vencimiento,
                    vencimiento.estado_presentacion,
                    vencimiento.estado_validacion or "",
                    vencimiento.responsable.nombre if vencimiento.responsable else "",
                ]
            )
            if (
                vencimiento.fecha_vencimiento < hoy
                and vencimiento.estado_presentacion != Vencimiento.PRESENTADA
            ):
                resaltadas.add(indice)
        presentadas = sum(1 for fila in filas if fila[6] == Vencimiento.PRESENTADA)
        return ResultadoReporte(
            secciones=[
                Seccion(
                    "Vencimientos",
                    columnas,
                    filas,
                    resaltadas,
                    nota_resaltado="En rojo: obligaciones vencidas sin presentar (HU029-4).",
                )
            ],
            resumen=[
                ("Obligaciones", str(len(filas))),
                ("Presentadas", str(presentadas)),
                ("Vencidas sin presentar", str(len(resaltadas))),
            ],
        )


# ---------------------------------------------------------------------------
# 3. Cartera
# ---------------------------------------------------------------------------


class ReporteCartera(DefinicionReporte):
    nombre = Reporte.CARTERA
    slug = "cartera"
    icono = "bi-wallet2"
    descripcion = (
        "Honorario, facturado, cobrado, deuda acumulada y mora por cliente, con el historial de abonos."
    )
    formulario = formularios.FiltroCarteraForm

    def generar(self, usuario, filtros, hoy=None):
        hoy = hoy or timezone.localdate()
        filas_cartera = selectores_finanzas.cartera(
            usuario, hoy=hoy, solo_con_saldo=not filtros.get("incluir_al_dia")
        )
        if filtros.get("cliente"):
            filas_cartera = [f for f in filas_cartera if f["cliente"] == filtros["cliente"]]
        if filtros.get("responsable"):
            filas_cartera = [
                f for f in filas_cartera if f["cliente"].responsable_id == filtros["responsable"].pk
            ]
        honorarios = {
            honorario.cliente_id: honorario
            for honorario in Honorario.objects.filter(cliente__in=[f["cliente"] for f in filas_cartera])
        }

        columnas = [
            Columna("Cliente", ancho=30),
            Columna("Honorario configurado", PESOS, ancho=16),
            Columna("Facturado", PESOS, ancho=14),
            Columna("Cobrado", PESOS, ancho=14),
            Columna("Deuda acumulada", PESOS, ancho=15),
            Columna("Cuentas pendientes", NUMERO, ancho=10),
            Columna("Días de mora", NUMERO, ancho=9),
            Columna("Indicador de mora", ancho=14),
        ]
        filas, resaltadas = [], set()
        for indice, fila in enumerate(filas_cartera):
            honorario = honorarios.get(fila["cliente"].pk)
            if fila["mora_critica"]:
                indicador = "Crítica"
                resaltadas.add(indice)
            elif fila["dias_mora"]:
                indicador = "En mora"
            elif fila["saldo"]:
                indicador = "Al día"
            else:
                indicador = "Sin deuda"
            filas.append(
                [
                    fila["cliente"].nombre_razon_social,
                    honorario.monto if honorario else None,
                    fila["facturado"],
                    fila["cobrado"],
                    fila["saldo"],
                    fila["cuentas_pendientes"],
                    fila["dias_mora"],
                    indicador,
                ]
            )

        abonos = _restringir(
            usuario,
            Abono.objects.select_related("cuenta_cobro__cliente", "metodo_pago", "responsable"),
            "cuenta_cobro__cliente__responsable",
        ).order_by("-fecha", "-id_abono")
        if filtros.get("cliente"):
            abonos = abonos.filter(cuenta_cobro__cliente=filtros["cliente"])
        if filtros.get("responsable"):
            abonos = abonos.filter(cuenta_cobro__cliente__responsable=filtros["responsable"])
        if filtros.get("desde"):
            abonos = abonos.filter(fecha__gte=filtros["desde"])
        if filtros.get("hasta"):
            abonos = abonos.filter(fecha__lte=filtros["hasta"])
        columnas_abonos = [
            Columna("Fecha", FECHA, ancho=11),
            Columna("Cliente", ancho=30),
            Columna("Cuenta No.", NUMERO, ancho=9),
            Columna("Medio de pago", ancho=16),
            Columna("Monto", PESOS, ancho=14),
            Columna("Saldo anterior", PESOS, ancho=14),
            Columna("Saldo resultante", PESOS, ancho=14),
            Columna("Registró", ancho=18),
        ]
        filas_abonos = [
            [
                abono.fecha,
                abono.cuenta_cobro.cliente.nombre_razon_social,
                abono.cuenta_cobro_id,
                abono.metodo_pago.nombre_metodo if abono.metodo_pago else "",
                abono.monto,
                abono.saldo_anterior,
                abono.saldo_resultante,
                abono.responsable.nombre if abono.responsable else "",
            ]
            for abono in abonos
        ]

        totales = selectores_finanzas.totales_cartera(filas_cartera)
        mayores = sorted(filas_cartera, key=lambda f: -f["saldo"])[:10]
        grafico = None
        if mayores:
            grafico = Grafico(
                "Deuda acumulada por cliente (10 mayores)",
                [f["cliente"].nombre_razon_social[:28] for f in mayores],
                [("Deuda acumulada", [float(f["saldo"]) for f in mayores])],
                horizontal=True,
            )
        return ResultadoReporte(
            secciones=[
                Seccion(
                    "Cartera por cliente",
                    columnas,
                    filas,
                    resaltadas,
                    nota_resaltado=f"En rojo: más de {selectores_finanzas.DIAS_MORA_CRITICA} días de mora.",
                ),
                Seccion("Historial de abonos", columnas_abonos, filas_abonos),
            ],
            resumen=[
                ("Facturado", formato_pesos(totales["facturado"])),
                ("Cobrado", formato_pesos(totales["cobrado"])),
                ("Deuda acumulada", formato_pesos(totales["saldo"])),
                ("Clientes en mora crítica", str(len(resaltadas))),
            ],
            grafico=grafico,
        )


# ---------------------------------------------------------------------------
# 4. Cuentas de cobro
# ---------------------------------------------------------------------------


class ReporteCuentasCobro(DefinicionReporte):
    nombre = Reporte.CUENTAS_COBRO
    slug = "cuentas-cobro"
    icono = "bi-receipt"
    descripcion = "Período facturado, valor, servicio, estados de envío y pago y vencimiento de cada cuenta."
    formulario = formularios.FiltroCuentasCobroForm

    def generar(self, usuario, filtros, hoy=None):
        consulta = selectores_finanzas.con_abonos(
            selectores_finanzas.cuentas_cobro_visibles(usuario)
        ).prefetch_related("detalles")
        for campo, filtro in (
            ("desde", "fecha_generacion__date__gte"),
            ("hasta", "fecha_generacion__date__lte"),
            ("cliente", "cliente"),
            ("responsable", "cliente__responsable"),
            ("estado_pago", "estado_pago"),
            ("estado_envio", "estado_envio"),
        ):
            if filtros.get(campo):
                consulta = consulta.filter(**{filtro: filtros[campo]})

        columnas = [
            Columna("No.", NUMERO, ancho=6),
            Columna("Cliente", ancho=26),
            Columna("Período facturado", ancho=22),
            Columna("Descripción del servicio", ancho=32),
            Columna("Valor", PESOS, ancho=13),
            Columna("Abonado", PESOS, ancho=13),
            Columna("Saldo", PESOS, ancho=13),
            Columna("Envío", ancho=10),
            Columna("Pago", ancho=10),
            Columna("Vence", FECHA, ancho=11),
        ]
        filas, resaltadas = [], set()
        for indice, cuenta in enumerate(consulta):
            periodo = cuenta.periodo_facturado
            if cuenta.fecha_inicio_periodo and cuenta.fecha_fin_periodo:
                periodo += f" ({cuenta.fecha_inicio_periodo:%d/%m/%Y} – {cuenta.fecha_fin_periodo:%d/%m/%Y})"
            filas.append(
                [
                    cuenta.pk,
                    cuenta.cliente.nombre_razon_social,
                    periodo,
                    "; ".join(detalle.descripcion_linea for detalle in cuenta.detalles.all()),
                    cuenta.valor_total,
                    cuenta.abonado,
                    cuenta.saldo,
                    cuenta.estado_envio,
                    cuenta.estado_pago,
                    cuenta.fecha_vencimiento_pago,
                ]
            )
            if cuenta.estado_pago == CuentaCobro.VENCIDA:
                resaltadas.add(indice)
        return ResultadoReporte(
            secciones=[
                Seccion("Cuentas de cobro", columnas, filas, resaltadas, "En rojo: cuentas vencidas.")
            ],
            resumen=[
                ("Cuentas", str(len(filas))),
                ("Valor total", formato_pesos(sum((fila[4] for fila in filas), Decimal("0")))),
                ("Saldo pendiente", formato_pesos(sum((fila[6] for fila in filas), Decimal("0")))),
                ("Vencidas", str(len(resaltadas))),
            ],
        )


# ---------------------------------------------------------------------------
# 5. Tareas del Kanban
# ---------------------------------------------------------------------------


class ReporteTareas(DefinicionReporte):
    nombre = Reporte.TAREAS
    slug = "tareas"
    icono = "bi-kanban-fill"
    descripcion = (
        "Tareas con cliente, tipo, responsable, prioridad, vencimiento, estado e historial de cambios."
    )
    formulario = formularios.FiltroTareasForm

    def generar(self, usuario, filtros, hoy=None):
        hoy = hoy or timezone.localdate()
        consulta = (
            Tarea.objects.select_related("cliente", "responsable")
            .prefetch_related("historial__usuario")
            .order_by("fecha_vencimiento", "cliente__nombre_razon_social")
        )
        for campo, filtro in (
            ("desde", "fecha_vencimiento__gte"),
            ("hasta", "fecha_vencimiento__lte"),
            ("cliente", "cliente"),
            ("responsable", "responsable"),
            ("estado", "estado"),
            ("prioridad", "prioridad"),
        ):
            if filtros.get(campo):
                consulta = consulta.filter(**{filtro: filtros[campo]})

        columnas = [
            Columna("Cliente", ancho=24),
            Columna("Tarea", ancho=26),
            Columna("Tipo", ancho=14),
            Columna("Responsable", ancho=18),
            Columna("Prioridad", ancho=9),
            Columna("Vence", FECHA, ancho=11),
            Columna("Estado", ancho=12),
            Columna("Historial de cambios", ancho=40),
        ]
        filas, resaltadas = [], set()
        for indice, tarea in enumerate(consulta):
            historial = "; ".join(
                f"{cambio.fecha_cambio:%d/%m/%Y} {cambio.usuario.nombre}: "
                f"{cambio.estado_anterior} → {cambio.estado_nuevo}"
                for cambio in tarea.historial.all()
            )
            filas.append(
                [
                    tarea.cliente.nombre_razon_social,
                    tarea.titulo,
                    tarea.tipo_tarea,
                    tarea.responsable.nombre if tarea.responsable else "Sin asignar",
                    tarea.prioridad,
                    tarea.fecha_vencimiento,
                    tarea.estado,
                    historial,
                ]
            )
            if tarea.fecha_vencimiento and tarea.fecha_vencimiento < hoy and tarea.estado != Tarea.TERMINADO:
                resaltadas.add(indice)
        terminadas = sum(1 for fila in filas if fila[6] == Tarea.TERMINADO)
        return ResultadoReporte(
            secciones=[
                Seccion("Tareas", columnas, filas, resaltadas, "En rojo: tareas vencidas sin terminar.")
            ],
            resumen=[
                ("Tareas", str(len(filas))),
                ("Terminadas", str(terminadas)),
                ("Pendientes", str(len(filas) - terminadas)),
                ("Vencidas", str(len(resaltadas))),
            ],
        )


# ---------------------------------------------------------------------------
# 6. Ingresos mensuales del despacho
# ---------------------------------------------------------------------------


def _variacion(actual, anterior):
    if not anterior:
        return None
    return float((Decimal(actual) - Decimal(anterior)) / Decimal(anterior) * 100)


class ReporteIngresos(DefinicionReporte):
    nombre = Reporte.INGRESOS
    slug = "ingresos"
    icono = "bi-graph-up-arrow"
    descripcion = (
        "Facturado, cobrado, pendiente y en mora por mes, con gráfica, comparativo, promedio y top 3."
    )
    formulario = formularios.FiltroIngresosForm

    def generar(self, usuario, filtros, hoy=None):
        hoy = hoy or timezone.localdate()
        hasta = filtros.get("hasta") or hoy
        desde = filtros.get("desde") or (hasta.replace(day=1) - relativedelta(months=11))
        meses = OrderedDict()
        mes = date(desde.year, desde.month, 1)
        while mes <= hasta:
            meses[(mes.year, mes.month)] = {
                "facturado": Decimal("0"),
                "cobrado": Decimal("0"),
                "pendiente": Decimal("0"),
                "mora": Decimal("0"),
            }
            mes += relativedelta(months=1)

        # Facturado, pendiente y en mora: cuentas generadas en el mes (saldo al día de hoy).
        cuentas = CuentaCobro.objects.filter(
            fecha_generacion__date__gte=date(desde.year, desde.month, 1), fecha_generacion__date__lte=hasta
        ).annotate(abonado=Coalesce(Sum("abonos__monto"), Decimal("0")))
        for cuenta in cuentas:
            fecha = timezone.localtime(cuenta.fecha_generacion).date()
            fila = meses.get((fecha.year, fecha.month))
            if fila is None:
                continue
            saldo = cuenta.valor_total - cuenta.abonado
            fila["facturado"] += cuenta.valor_total
            if saldo > 0:
                fila["mora" if cuenta.fecha_vencimiento_pago < hoy else "pendiente"] += saldo
        # Cobrado: abonos recibidos en el mes (lo que efectivamente ingresó).
        for abono in Abono.objects.filter(fecha__gte=date(desde.year, desde.month, 1), fecha__lte=hasta):
            fila = meses.get((abono.fecha.year, abono.fecha.month))
            if fila is not None:
                fila["cobrado"] += abono.monto

        etiquetas = [f"{MESES[m - 1]} {a}" for a, m in meses]
        valores = list(meses.values())
        columnas = [
            Columna("Mes", ancho=12),
            Columna("Facturado", PESOS, ancho=15),
            Columna("Cobrado", PESOS, ancho=15),
            Columna("Pendiente", PESOS, ancho=15),
            Columna("En mora", PESOS, ancho=15),
        ]
        filas = [
            [etiqueta, v["facturado"], v["cobrado"], v["pendiente"], v["mora"]]
            for etiqueta, v in zip(etiquetas, valores, strict=True)
        ]
        cantidad = len(valores) or 1
        promedio_facturado = sum((v["facturado"] for v in valores), Decimal("0")) / cantidad
        promedio_cobrado = sum((v["cobrado"] for v in valores), Decimal("0")) / cantidad

        comparativo = []
        if len(valores) >= 2:
            actual, anterior = valores[-1], valores[-2]
            for concepto in ("facturado", "cobrado", "pendiente", "mora"):
                comparativo.append(
                    [
                        concepto.capitalize() if concepto != "mora" else "En mora",
                        anterior[concepto],
                        actual[concepto],
                        _variacion(actual[concepto], anterior[concepto]),
                    ]
                )

        cartera_total = selectores_finanzas.cartera(_UsuarioConsolidado(), hoy=hoy)
        top3 = sorted(cartera_total, key=lambda f: -f["saldo"])[:3]

        secciones = [Seccion("Ingresos por mes", columnas, filas)]
        if comparativo:
            secciones.append(
                Seccion(
                    f"Comparativo: {etiquetas[-1]} frente a {etiquetas[-2]}",
                    [
                        Columna("Concepto", ancho=14),
                        Columna(etiquetas[-2], PESOS, ancho=15),
                        Columna(etiquetas[-1], PESOS, ancho=15),
                        Columna("Variación", PORCENTAJE, ancho=11),
                    ],
                    comparativo,
                )
            )
        secciones.append(
            Seccion(
                "Tres clientes con mayor saldo pendiente",
                [
                    Columna("Cliente", ancho=30),
                    Columna("Saldo pendiente", PESOS, ancho=16),
                    Columna("Días de mora", NUMERO),
                ],
                [[f["cliente"].nombre_razon_social, f["saldo"], f["dias_mora"]] for f in top3],
            )
        )
        return ResultadoReporte(
            secciones=secciones,
            resumen=[
                ("Promedio mensual facturado", formato_pesos(promedio_facturado)),
                ("Promedio mensual cobrado", formato_pesos(promedio_cobrado)),
                (
                    "Total cobrado en el rango",
                    formato_pesos(sum((v["cobrado"] for v in valores), Decimal("0"))),
                ),
                ("Saldo en mora", formato_pesos(sum((v["mora"] for v in valores), Decimal("0")))),
            ],
            grafico=Grafico(
                "Evolución mensual",
                etiquetas,
                [
                    ("Facturado", [float(v["facturado"]) for v in valores]),
                    ("Cobrado", [float(v["cobrado"]) for v in valores]),
                    ("Pendiente", [float(v["pendiente"]) for v in valores]),
                    ("En mora", [float(v["mora"]) for v in valores]),
                ],
            ),
            notas=[
                "Facturado: cuentas de cobro generadas en el mes. Cobrado: abonos recibidos en el mes.",
                "Pendiente y en mora: saldo actual de las cuentas generadas en el mes, "
                "según si ya vencieron.",
            ],
        )


class _UsuarioConsolidado:
    """Usuario ficticio con vista de Administrador: el reporte de ingresos es del despacho completo."""

    es_administrador = True


REPORTES = [
    ReporteClientes(),
    ReporteVencimientos(),
    ReporteCartera(),
    ReporteCuentasCobro(),
    ReporteTareas(),
    ReporteIngresos(),
]
POR_SLUG = {definicion.slug: definicion for definicion in REPORTES}
