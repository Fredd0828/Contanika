"""
Tablero del panel principal: resumen gráfico del trabajo del despacho.

Cada sección reúne los datos de un módulo usando los mismos selectores de
visibilidad de ese módulo, de modo que el panel nunca muestra más de lo que
el usuario vería al entrar al módulo. Una sección solo se arma si el rol
tiene el módulo habilitado (RQF031); si no, queda en None y la plantilla la
omite.
"""

from datetime import timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Case, Count, F, IntegerField, Q, Sum, Value, When
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone

from aplicaciones.comunes import paleta

from . import selectores
from .models import Modulo

SEMANAS_GRAFICO = 8  # semanas de carga de vencimientos, contando la actual
MESES_GRAFICO = 6  # meses de facturado y cobrado, contando el actual
DIAS_PROXIMOS = 7
LIMITE_LISTA = 6
LIMITE_VENCIMIENTOS = 5
LIMITE_ATRASADOS = 2  # vencidos que encabezan la lista de vencimientos
LIMITE_DEUDORES = 4
LIMITE_HALLAZGOS = 4
LIMITE_EQUIPO = 6

MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _porcentaje(parte, total):
    """Porcentaje entero de `parte` sobre `total`; None si no hay total."""
    return round(100 * parte / total) if total else None


def _anchos(filas, campo="cantidad"):
    """Agrega a cada fila el ancho de su barra (0-100), relativo a la fila mayor."""
    mayor = max((fila[campo] for fila in filas), default=0)
    for fila in filas:
        fila["ancho"] = round(100 * fila[campo] / mayor) if mayor else 0
    return filas


def _dia_mes(fecha):
    return f"{fecha.day} {MESES_CORTOS[fecha.month - 1]}"


def _plural(cantidad, palabra):
    return palabra if cantidad == 1 else f"{palabra}s"


def _pesos_abreviado(valor):
    """Monto abreviado para las cifras de la franja superior: `$ 18,8 M` o `$ 845 mil`."""
    from aplicaciones.finanzas.templatetags.finanzas_tags import formato_pesos

    valor = Decimal(valor or 0)
    if abs(valor) >= 1_000_000:
        return f"$ {valor / 1_000_000:.1f} M".replace(".", ",")
    if abs(valor) >= 1_000:
        return f"$ {valor / 1_000:.0f} mil"
    return formato_pesos(valor)


# ---------------------------------------------------------------------------
# Vencimientos (Módulo 2)
# ---------------------------------------------------------------------------


def seccion_vencimientos(usuario, hoy):
    """
    Vencidos sin presentar, los de los próximos 7 días, cumplimiento del mes,
    carga por semana de las próximas 8 semanas y lista de lo más urgente.
    """
    from aplicaciones.calendario.models import Vencimiento
    from aplicaciones.calendario.selectores import vencimientos_visibles

    base = vencimientos_visibles(usuario).prefetch_related(None)
    por_presentar = ~Q(estado_presentacion=Vencimiento.PRESENTADA)
    del_mes = Q(fecha_vencimiento__year=hoy.year, fecha_vencimiento__month=hoy.month)
    totales = base.aggregate(
        vencidos=Count("pk", filter=por_presentar & Q(fecha_vencimiento__lt=hoy)),
        proximos=Count(
            "pk",
            filter=por_presentar & Q(fecha_vencimiento__range=(hoy, hoy + timedelta(days=DIAS_PROXIMOS))),
        ),
        del_mes=Count("pk", filter=del_mes),
        presentados_mes=Count("pk", filter=del_mes & Q(estado_presentacion=Vencimiento.PRESENTADA)),
    )

    # Carga por semana (de lunes a domingo), desde la semana en curso.
    lunes = hoy - timedelta(days=hoy.weekday())
    semanas = []
    for indice in range(SEMANAS_GRAFICO):
        inicio = lunes + timedelta(weeks=indice)
        semanas.append(
            {
                "etiqueta": _dia_mes(inicio),
                "inicio": inicio,
                "fin": inicio + timedelta(days=6),
                "por_presentar": 0,
                "presentados": 0,
            }
        )
    conteos = (
        base.filter(fecha_vencimiento__range=(lunes, semanas[-1]["fin"]))
        .order_by()
        .values("fecha_vencimiento", "estado_presentacion")
        .annotate(cantidad=Count("pk"))
    )
    for conteo in conteos:
        semana = semanas[(conteo["fecha_vencimiento"] - lunes).days // 7]
        presentado = conteo["estado_presentacion"] == Vencimiento.PRESENTADA
        semana["presentados" if presentado else "por_presentar"] += conteo["cantidad"]

    # Lo más urgente: los vencidos más recientes y, después, los que siguen.
    pendientes = base.exclude(estado_presentacion=Vencimiento.PRESENTADA)
    atrasados = list(
        pendientes.filter(fecha_vencimiento__lt=hoy).order_by("-fecha_vencimiento")[:LIMITE_ATRASADOS]
    )
    siguientes = list(
        pendientes.filter(fecha_vencimiento__gte=hoy).order_by(
            "fecha_vencimiento", "cliente__nombre_razon_social"
        )[: LIMITE_VENCIMIENTOS - len(atrasados)]
    )
    lista = []
    for vencimiento in atrasados[::-1] + siguientes:
        dias = (vencimiento.fecha_vencimiento - hoy).days
        lista.append({"vencimiento": vencimiento, "dias": dias, "dias_atraso": -dias if dias < 0 else 0})

    return {
        "vencidos": totales["vencidos"],
        "proximos": totales["proximos"],
        "del_mes": totales["del_mes"],
        "presentados_mes": totales["presentados_mes"],
        "cumplimiento_mes": _porcentaje(totales["presentados_mes"], totales["del_mes"]),
        "semanas": semanas,
        "hay_semanas": any(semana["por_presentar"] or semana["presentados"] for semana in semanas),
        "lista": lista,
        "grafico": {
            "etiquetas": [semana["etiqueta"] for semana in semanas],
            "series": [
                {
                    "nombre": "Por presentar",
                    "valores": [semana["por_presentar"] for semana in semanas],
                    "color": paleta.NARANJA,
                },
                {
                    "nombre": "Presentados",
                    "valores": [semana["presentados"] for semana in semanas],
                    "color": paleta.VERDE,
                },
            ],
        },
    }


# ---------------------------------------------------------------------------
# Tareas (Módulo 3)
# ---------------------------------------------------------------------------


def seccion_tareas(usuario, hoy):
    """
    Tareas por columna del Kanban, atrasadas y las próximas del usuario; si no
    tiene ninguna asignada, las próximas de las tareas que puede ver.
    """
    from aplicaciones.tareas.models import Tarea
    from aplicaciones.tareas.selectores import tareas_visibles

    base = tareas_visibles(usuario)
    conteo = dict(base.order_by().values_list("estado").annotate(cantidad=Count("pk")))
    por_estado = _anchos(
        [{"estado": estado, "cantidad": conteo.get(estado, 0)} for estado, _ in Tarea.OPCIONES_ESTADO]
    )
    total = sum(fila["cantidad"] for fila in por_estado)
    terminadas = conteo.get(Tarea.TERMINADO, 0)

    activas = base.exclude(estado=Tarea.TERMINADO)
    por_fecha = (F("fecha_vencimiento").asc(nulls_last=True), "id_tarea")
    propias = list(activas.filter(responsable=usuario).order_by(*por_fecha)[:LIMITE_LISTA])
    proximas = propias or list(activas.order_by(*por_fecha)[:LIMITE_LISTA])
    lista = [
        {"tarea": tarea, "atrasada": bool(tarea.fecha_vencimiento and tarea.fecha_vencimiento < hoy)}
        for tarea in proximas
    ]

    return {
        "por_estado": por_estado,
        "total": total,
        "activas": total - terminadas,
        "atrasadas": activas.filter(fecha_vencimiento__lt=hoy).count(),
        "avance": _porcentaje(terminadas, total),
        "lista": lista,
        "lista_propia": bool(propias),
    }


# ---------------------------------------------------------------------------
# Finanzas (Módulo 6)
# ---------------------------------------------------------------------------


def seccion_finanzas(usuario, hoy):
    """
    Cartera por cobrar y en mora, facturado y cobrado de los últimos 6 meses y
    clientes con mayor mora. El Administrador ve el despacho completo; Senior
    y Junior, solo sus clientes asignados (HU016-HU018).
    """
    from aplicaciones.finanzas import selectores as selectores_finanzas
    from aplicaciones.finanzas.models import Abono

    visibles = selectores_finanzas.cuentas_cobro_visibles(usuario)
    primer_mes = hoy.replace(day=1) - relativedelta(months=MESES_GRAFICO - 1)
    meses = {}
    for indice in range(MESES_GRAFICO):
        mes = primer_mes + relativedelta(months=indice)
        meses[(mes.year, mes.month)] = {
            "etiqueta": f"{MESES_CORTOS[mes.month - 1]} {mes:%y}",
            "facturado": Decimal("0"),
            "cobrado": Decimal("0"),
        }

    facturado = cobrado = en_mora = Decimal("0")
    cuentas = visibles.select_related(None).annotate(abonado=Coalesce(Sum("abonos__monto"), Decimal("0")))
    for cuenta in cuentas:
        saldo_cuenta = cuenta.valor_total - cuenta.abonado
        facturado += cuenta.valor_total
        cobrado += cuenta.abonado
        if saldo_cuenta > 0 and cuenta.fecha_vencimiento_pago < hoy:
            en_mora += saldo_cuenta
        # Facturado del mes: cuentas generadas en ese mes.
        generada = timezone.localtime(cuenta.fecha_generacion).date()
        mes = meses.get((generada.year, generada.month))
        if mes is not None:
            mes["facturado"] += cuenta.valor_total
    # Cobrado del mes: abonos recibidos en ese mes (lo que efectivamente ingresó).
    abonos = Abono.objects.filter(cuenta_cobro__in=visibles, fecha__gte=primer_mes)
    for fecha, monto in abonos.values_list("fecha", "monto"):
        mes = meses.get((fecha.year, fecha.month))
        if mes is not None:
            mes["cobrado"] += monto

    filas_meses = list(meses.values())
    mes_actual = filas_meses[-1]
    return {
        "consolidado": usuario.es_administrador,
        "saldo": facturado - cobrado,
        "en_mora": en_mora,
        "facturado_mes": mes_actual["facturado"],
        "cobrado_mes": mes_actual["cobrado"],
        "recaudo": _porcentaje(cobrado, facturado),
        "deudores": selectores_finanzas.cartera(usuario, hoy=hoy)[:LIMITE_DEUDORES],
        "meses": filas_meses,
        "hay_meses": any(mes["facturado"] or mes["cobrado"] for mes in filas_meses),
        "grafico": {
            "etiquetas": [mes["etiqueta"] for mes in filas_meses],
            "series": [
                {
                    "nombre": "Facturado",
                    "valores": [float(mes["facturado"]) for mes in filas_meses],
                    "color": paleta.TEAL,
                },
                {
                    "nombre": "Cobrado",
                    "valores": [float(mes["cobrado"]) for mes in filas_meses],
                    "color": paleta.NARANJA,
                },
            ],
        },
    }


# ---------------------------------------------------------------------------
# Hallazgos (Módulo 5), clientes (Módulo 1) y equipo (Módulo 8)
# ---------------------------------------------------------------------------


def seccion_hallazgos(usuario):
    """Hallazgos sin cerrar: por estado, por prioridad y los más prioritarios."""
    from aplicaciones.hallazgos.models import Hallazgo
    from aplicaciones.hallazgos.selectores import hallazgos_visibles

    abiertos = hallazgos_visibles(usuario).exclude(estado=Hallazgo.CERRADO)
    por_estado = dict(abiertos.order_by().values_list("estado").annotate(cantidad=Count("pk")))
    por_prioridad = dict(abiertos.order_by().values_list("prioridad").annotate(cantidad=Count("pk")))
    orden_prioridad = Case(
        When(prioridad=Hallazgo.ALTA, then=Value(0)),
        When(prioridad=Hallazgo.MEDIA, then=Value(1)),
        default=Value(2),
        output_field=IntegerField(),
    )
    return {
        "abiertos": sum(por_estado.values()),
        "alta": por_prioridad.get(Hallazgo.ALTA, 0),
        "por_estado": _anchos(
            [
                {"estado": estado, "cantidad": por_estado.get(estado, 0)}
                for estado in (Hallazgo.ABIERTO, Hallazgo.EN_PROCESO, Hallazgo.PENDIENTE_CLIENTE)
            ]
        ),
        "por_prioridad": [
            {"prioridad": prioridad, "cantidad": por_prioridad.get(prioridad, 0)}
            for prioridad, _ in Hallazgo.OPCIONES_PRIORIDAD
        ],
        "lista": list(
            abiertos.annotate(orden_prioridad=orden_prioridad).order_by(
                "orden_prioridad", "fecha_fin_periodo", "id_hallazgo"
            )[:LIMITE_HALLAZGOS]
        ),
    }


def seccion_clientes(hoy):
    """Clientes activos y los registrados en el mes en curso."""
    from aplicaciones.clientes.models import Cliente

    return Cliente.objects.aggregate(
        activos=Count("pk", filter=Q(estado=Cliente.ACTIVO)),
        nuevos_mes=Count("pk", filter=Q(fecha_registro__year=hoy.year, fecha_registro__month=hoy.month)),
    )


def seccion_equipo(hoy):
    """Carga de trabajo por miembro, la misma del panel de equipo (HU023)."""
    miembros = _anchos(selectores.resumen_equipo(hoy)[:LIMITE_EQUIPO], "tareas_activas")
    return {"miembros": miembros, "limite_pendientes": selectores.LIMITE_TAREAS_PENDIENTES}


# ---------------------------------------------------------------------------
# Tablero completo
# ---------------------------------------------------------------------------


def _indicadores(tablero):
    """Cifras de la franja superior, una o dos por sección disponible, con enlace al módulo."""
    from aplicaciones.finanzas.templatetags.finanzas_tags import formato_pesos

    indicadores = []
    vencimientos = tablero["vencimientos"]
    if vencimientos:
        indicadores.append(
            {
                "etiqueta": f"Vencen en {DIAS_PROXIMOS} días",
                "valor": vencimientos["proximos"],
                "detalle": "Obligaciones por presentar",
                "icono": "bi-calendar2-week",
                "tono": "naranja" if vencimientos["proximos"] else "teal",
                "url": reverse("calendario:lista"),
            }
        )
        indicadores.append(
            {
                "etiqueta": "Vencidos sin presentar",
                "valor": vencimientos["vencidos"],
                "detalle": "Requieren atención" if vencimientos["vencidos"] else "Todo al día",
                "icono": "bi-exclamation-triangle" if vencimientos["vencidos"] else "bi-check2-circle",
                "tono": "rojo" if vencimientos["vencidos"] else "verde",
                "url": reverse("calendario:lista"),
            }
        )
    tareas = tablero["tareas"]
    if tareas:
        indicadores.append(
            {
                "etiqueta": "Tareas atrasadas",
                "valor": tareas["atrasadas"],
                "detalle": f"{tareas['activas']} {_plural(tareas['activas'], 'activa')} en el tablero",
                "icono": "bi-kanban",
                "tono": "rojo" if tareas["atrasadas"] else "teal",
                "url": reverse("tareas:tablero"),
            }
        )
    finanzas = tablero["finanzas"]
    if finanzas:
        indicadores.append(
            {
                "etiqueta": "Cartera por cobrar",
                "valor": _pesos_abreviado(finanzas["saldo"]),
                "exacto": formato_pesos(finanzas["saldo"]),
                "detalle": (
                    f"{formato_pesos(finanzas['en_mora'])} en mora"
                    if finanzas["en_mora"]
                    else "Sin cuentas en mora"
                ),
                "icono": "bi-wallet2",
                "tono": "rojo" if finanzas["en_mora"] else "teal",
                "url": reverse("finanzas:cartera"),
            }
        )
    hallazgos = tablero["hallazgos"]
    if hallazgos:
        indicadores.append(
            {
                "etiqueta": "Hallazgos abiertos",
                "valor": hallazgos["abiertos"],
                "detalle": f"{hallazgos['alta']} de prioridad alta",
                "icono": "bi-search",
                "tono": "naranja" if hallazgos["alta"] else "teal",
                "url": reverse("hallazgos:lista"),
            }
        )
    clientes = tablero["clientes"]
    if clientes:
        indicadores.append(
            {
                "etiqueta": "Clientes activos",
                "valor": clientes["activos"],
                "detalle": f"{clientes['nuevos_mes']} {_plural(clientes['nuevos_mes'], 'nuevo')} este mes",
                "icono": "bi-people",
                "tono": "teal",
                "url": reverse("clientes:lista"),
            }
        )
    return indicadores


def armar_tablero(usuario, hoy=None):
    """Secciones del panel principal para el usuario; None en las de módulos inhabilitados."""
    hoy = hoy or timezone.localdate()
    habilitado = usuario.tiene_modulo_habilitado
    ve_equipo = usuario.es_administrador or usuario.es_contador_senior
    tablero = {
        "hoy": hoy,
        "vencimientos": seccion_vencimientos(usuario, hoy) if habilitado(Modulo.MOD02_CALENDARIO) else None,
        "tareas": seccion_tareas(usuario, hoy) if habilitado(Modulo.MOD03_TAREAS) else None,
        "finanzas": seccion_finanzas(usuario, hoy) if habilitado(Modulo.MOD06_FINANZAS) else None,
        "hallazgos": seccion_hallazgos(usuario) if habilitado(Modulo.MOD05_HALLAZGOS) else None,
        "clientes": seccion_clientes(hoy) if habilitado(Modulo.MOD01_CLIENTES) else None,
        "equipo": seccion_equipo(hoy) if ve_equipo and habilitado(Modulo.MOD08_EQUIPO) else None,
    }
    tablero["indicadores"] = _indicadores(tablero)
    return tablero
