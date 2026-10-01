"""
Consultas del módulo 6: honorarios, cartera y cuentas de cobro.

Visibilidad (HU016-HU018): el Administrador ve la información financiera de
todos los clientes; el Contador Senior y el Contador Junior solo la de los
clientes que tienen asignados como responsables, y únicamente en consulta.
"""

from decimal import Decimal

from django.db.models import F, Prefetch, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from aplicaciones.clientes.models import Cliente

from .models import Abono, CuentaCobro, EnvioProgramado, Honorario


def _restringir_a_asignados(usuario, consulta, campo_responsable):
    """Limita la consulta a los clientes asignados cuando el usuario no es Administrador."""
    if usuario.es_administrador:
        return consulta
    return consulta.filter(**{campo_responsable: usuario})


def clientes_para_cobro(usuario):
    """Clientes activos a los que el usuario puede generar cuentas de cobro."""
    consulta = Cliente.objects.filter(estado=Cliente.ACTIVO).order_by("nombre_razon_social")
    return _restringir_a_asignados(usuario, consulta, "responsable")


def cuentas_cobro_visibles(usuario):
    """Cuentas de cobro que el usuario puede consultar."""
    consulta = CuentaCobro.objects.select_related("cliente", "cuenta_bancaria", "metodo_pago")
    return _restringir_a_asignados(usuario, consulta, "cliente__responsable")


def con_abonos(consulta):
    """
    Agrega a cada cuenta de cobro lo abonado (`abonado`), el saldo pendiente
    (`saldo`) y sus abonos en orden cronológico, para mostrarlos en tablas
    sin una consulta por fila. El orden se fija explícitamente porque Django
    no aplica el `ordering` del modelo en consultas agregadas.
    """
    return (
        consulta.annotate(abonado=Coalesce(Sum("abonos__monto"), Decimal("0")))
        .annotate(saldo=F("valor_total") - F("abonado"))
        .order_by("-fecha_generacion", "-id_cuenta_cobro")
        .prefetch_related(
            Prefetch(
                "abonos", queryset=Abono.objects.select_related("metodo_pago").order_by("fecha", "id_abono")
            )
        )
    )


def filtrar_cuentas_cobro(usuario, cliente=None, estado_pago=None, periodo=None, desde=None, hasta=None):
    """Aplica los filtros desplegables del histórico; todos son opcionales."""
    consulta = con_abonos(cuentas_cobro_visibles(usuario))
    if cliente:
        consulta = consulta.filter(cliente=cliente)
    if estado_pago:
        consulta = consulta.filter(estado_pago=estado_pago)
    if periodo:
        consulta = consulta.filter(periodo_facturado=periodo)
    if desde:
        consulta = consulta.filter(fecha_generacion__date__gte=desde)
    if hasta:
        consulta = consulta.filter(fecha_generacion__date__lte=hasta)
    return consulta


def cuentas_del_cliente(usuario, cliente, limite=10):
    """Últimas cuentas de cobro de un cliente, para el panel de su ficha."""
    return con_abonos(cuentas_cobro_visibles(usuario).filter(cliente=cliente))[:limite]


def honorario_del_cliente(cliente):
    """Honorario configurado del cliente, o None si todavía no tiene."""
    return (
        Honorario.objects.select_related("usuario_actualizacion")
        .prefetch_related("servicios__tipo_servicio")
        .filter(cliente=cliente)
        .first()
    )


def tipos_servicio_del_cliente(cliente):
    """Tipos de servicio contable asociados al cliente (Módulo 1)."""
    return [relacion.tipo_servicio for relacion in cliente.servicios.select_related("tipo_servicio")]


def sugerencia_cuenta_cobro(cliente):
    """
    Valor total y líneas de servicio sugeridas para una cuenta de cobro nueva
    (HU049): una línea por cada tipo de servicio del cliente; si el honorario
    es por servicio, cada línea lleva el monto configurado para ese servicio.
    """
    honorario = honorario_del_cliente(cliente)
    montos = {}
    if honorario and honorario.tipo == Honorario.POR_SERVICIO:
        montos = {linea.tipo_servicio_id: linea.monto for linea in honorario.servicios.all()}
    lineas = [
        {
            "descripcion_linea": tipo.nombre_servicio,
            "valor_linea": montos.get(tipo.pk) or None,
        }
        for tipo in tipos_servicio_del_cliente(cliente)
    ]
    return {
        "valor_total": honorario.monto if honorario else Decimal("0"),
        "lineas": lineas,
    }


# ---------------------------------------------------------------------------
# Abonos y cartera (HU016-HU018)
# ---------------------------------------------------------------------------

DIAS_MORA_CRITICA = 30  # más de 30 días en mora: indicador rojo (HU017-3)


def abonos_del_cliente(usuario, cliente):
    """Historial de abonos de un cliente, del más reciente al más antiguo (HU018)."""
    consulta = Abono.objects.filter(cuenta_cobro__cliente=cliente).select_related(
        "cuenta_cobro", "metodo_pago", "responsable"
    )
    return _restringir_a_asignados(usuario, consulta, "cuenta_cobro__cliente__responsable").order_by(
        "-fecha", "-id_abono"
    )


def saldo_del_cliente(cliente):
    """Saldo pendiente total del cliente: facturado menos abonado en todas sus cuentas."""
    facturado = CuentaCobro.objects.filter(cliente=cliente).aggregate(total=Sum("valor_total"))["total"] or 0
    abonado = Abono.objects.filter(cuenta_cobro__cliente=cliente).aggregate(total=Sum("monto"))["total"] or 0
    return facturado - abonado


def cartera(usuario, hoy=None, solo_con_saldo=True):
    """
    Panel de cartera por cliente (HU016-4, HU017): valor facturado, cobrado,
    saldo pendiente, cuentas pendientes y días en mora (los de la cuenta con
    saldo más atrasada). Ordenado de mayor a menor mora y luego por saldo.
    """
    hoy = hoy or timezone.localdate()
    cuentas = cuentas_cobro_visibles(usuario).annotate(abonado=Coalesce(Sum("abonos__monto"), Decimal("0")))
    filas = {}
    for cuenta in cuentas:
        fila = filas.setdefault(
            cuenta.cliente_id,
            {
                "cliente": cuenta.cliente,
                "facturado": Decimal("0"),
                "cobrado": Decimal("0"),
                "saldo": Decimal("0"),
                "cuentas_pendientes": 0,
                "dias_mora": 0,
            },
        )
        saldo_cuenta = cuenta.valor_total - cuenta.abonado
        fila["facturado"] += cuenta.valor_total
        fila["cobrado"] += cuenta.abonado
        fila["saldo"] += saldo_cuenta
        if saldo_cuenta > 0:
            fila["cuentas_pendientes"] += 1
            if cuenta.fecha_vencimiento_pago < hoy:
                fila["dias_mora"] = max(fila["dias_mora"], (hoy - cuenta.fecha_vencimiento_pago).days)
    resultado = [fila for fila in filas.values() if fila["saldo"] > 0 or not solo_con_saldo]
    for fila in resultado:
        fila["mora_critica"] = fila["dias_mora"] > DIAS_MORA_CRITICA
    return sorted(resultado, key=lambda fila: (-fila["dias_mora"], -fila["saldo"]))


def totales_cartera(filas):
    """Totales del panel de cartera (facturado, cobrado y saldo)."""
    return {
        campo: sum((fila[campo] for fila in filas), Decimal("0"))
        for campo in ("facturado", "cobrado", "saldo")
    }


# ---------------------------------------------------------------------------
# Envíos
# ---------------------------------------------------------------------------


def envios_de_cuenta(cuenta):
    """Historial de envíos (hechos, fallidos y programados) de una cuenta de cobro."""
    return cuenta.envios_programados.select_related("usuario", "comunicacion").order_by("-fecha_programada")


def bandeja_whatsapp():
    """WhatsApp que ya llegaron a su hora y esperan que alguien pulse "Enviar"."""
    return (
        EnvioProgramado.objects.filter(estado=EnvioProgramado.PENDIENTE_WHATSAPP)
        .select_related("cuenta_cobro__cliente")
        .order_by("fecha_programada")
    )


def envios_programados(estado=None):
    """Envíos programados para el listado de control, filtrables por estado."""
    consulta = EnvioProgramado.objects.select_related("cuenta_cobro__cliente", "usuario")
    if estado:
        consulta = consulta.filter(estado=estado)
    return consulta


def cuentas_para_envio_masivo(usuario, tipo, incluir_enviadas=False):
    """
    Cuentas candidatas al envío masivo (HU046, HU047): para enviar cuentas de
    cobro, las que aún no se han enviado o cuyo envío falló (o todas, si se
    pide reenviar también las ya enviadas); para recordatorios, las que
    tienen saldo pendiente. Ordenadas por cliente y de la más reciente a la
    más antigua.
    """
    consulta = con_abonos(cuentas_cobro_visibles(usuario).filter(cliente__estado=Cliente.ACTIVO)).order_by(
        "cliente__nombre_razon_social", "-fecha_generacion"
    )
    if tipo == EnvioProgramado.RECORDATORIO:
        return list(consulta.filter(saldo__gt=0))
    if not incluir_enviadas:
        consulta = consulta.exclude(estado_envio=CuentaCobro.ENVIADA)
    return list(consulta)
