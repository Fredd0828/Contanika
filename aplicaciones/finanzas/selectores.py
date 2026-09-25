"""
Consultas del módulo 6: honorarios, cartera y cuentas de cobro.

Visibilidad (HU016-HU018): el Administrador ve la información financiera de
todos los clientes; el Contador Senior y el Contador Junior solo la de los
clientes que tienen asignados como responsables, y únicamente en consulta.
"""

from decimal import Decimal

from aplicaciones.clientes.models import Cliente

from .models import CuentaCobro, EnvioProgramado, Honorario


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


def filtrar_cuentas_cobro(usuario, cliente=None, estado_pago=None, periodo=None, desde=None, hasta=None):
    """Aplica los filtros desplegables del histórico; todos son opcionales."""
    consulta = cuentas_cobro_visibles(usuario)
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
    return cuentas_cobro_visibles(usuario).filter(cliente=cliente)[:limite]


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


def cuentas_para_envio_masivo(usuario, tipo):
    """
    Cuentas candidatas al envío masivo (HU046, HU047): para enviar cuentas de
    cobro, las que aún no se han enviado o cuyo envío falló; para
    recordatorios, las que tienen saldo pendiente.
    """
    consulta = cuentas_cobro_visibles(usuario).filter(cliente__estado=Cliente.ACTIVO)
    if tipo == EnvioProgramado.RECORDATORIO:
        pendientes = consulta.exclude(estado_pago=CuentaCobro.PAGADA)
        return [cuenta for cuenta in pendientes if cuenta.saldo_pendiente > 0]
    return list(consulta.exclude(estado_envio=CuentaCobro.ENVIADA))
