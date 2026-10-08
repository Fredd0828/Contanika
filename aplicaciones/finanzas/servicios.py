"""
Reglas de negocio del módulo 6: honorarios, catálogos y cuentas de cobro.

Las vistas no escriben directamente en varios modelos ni arman el PDF: llaman
a estas funciones, que agrupan cada operación en una transacción para que la
cuenta de cobro (con sus líneas y su archivo) o el honorario (con sus montos
por servicio) queden consistentes.
"""

import io
from datetime import timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.html import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from aplicaciones.clientes.models import Cliente
from aplicaciones.comunes import paleta
from aplicaciones.comunes.pdf import encabezado_despacho
from aplicaciones.seguridad.models import ConfiguracionDespacho

from . import envios, selectores
from .models import (
    AMBOS,
    CORREO,
    WHATSAPP,
    Abono,
    ConfiguracionCobro,
    CuentaCobro,
    CuentaCobroDetalle,
    EnvioProgramado,
    Honorario,
    HonorarioServicio,
    MetodoPago,
)
from .templatetags.finanzas_tags import formato_pesos

MESES_POR_PERIODO = {
    CuentaCobro.MENSUAL: 1,
    CuentaCobro.BIMESTRAL: 2,
    CuentaCobro.TRIMESTRAL: 3,
    CuentaCobro.SEMESTRAL: 6,
    CuentaCobro.ANUAL: 12,
}


# ---------------------------------------------------------------------------
# Honorario del cliente (HU044)
# ---------------------------------------------------------------------------


@transaction.atomic
def configurar_honorario(cliente, tipo, monto, montos_por_servicio, usuario):
    """
    Crea o actualiza el honorario del cliente.

    Si es "Por servicio", guarda un monto por cada tipo de servicio recibido
    en `montos_por_servicio` (`{tipo_servicio: monto}`) y el monto total del
    honorario pasa a ser la suma de esas líneas. Si es "Fijo mensual", se
    conserva solo el monto indicado y se descartan los montos por servicio.
    Las cuentas de cobro ya generadas no cambian: guardan su propio valor.
    """
    honorario, _ = Honorario.objects.get_or_create(cliente=cliente)
    honorario.tipo = tipo
    honorario.usuario_actualizacion = usuario

    if tipo == Honorario.POR_SERVICIO:
        honorario.servicios.exclude(tipo_servicio__in=montos_por_servicio.keys()).delete()
        for tipo_servicio, monto_servicio in montos_por_servicio.items():
            HonorarioServicio.objects.update_or_create(
                honorario=honorario,
                tipo_servicio=tipo_servicio,
                defaults={"monto": monto_servicio or Decimal("0")},
            )
        honorario.monto = sum((m or Decimal("0") for m in montos_por_servicio.values()), Decimal("0"))
    else:
        honorario.servicios.all().delete()
        honorario.monto = monto or Decimal("0")

    honorario.save()
    return honorario


# ---------------------------------------------------------------------------
# Catálogos (conceptos facturables, cuentas bancarias, métodos de pago)
# ---------------------------------------------------------------------------


def eliminar_elemento_catalogo(elemento):
    """
    Elimina un elemento de catálogo. Si ya está usado en cuentas de cobro o
    abonos (relación protegida), se convierte en un error de negocio legible.
    """
    try:
        elemento.delete()
    except ProtectedError as error:
        raise ValueError("No se puede eliminar porque ya está usado en cuentas de cobro o abonos.") from error


# ---------------------------------------------------------------------------
# Cuentas de cobro (HU016, HU049)
# ---------------------------------------------------------------------------


def calcular_fin_periodo(periodo_facturado, fecha_inicio):
    """
    Último día del período facturado a partir de su fecha de inicio; por
    ejemplo, un período trimestral que empieza el 1 de enero termina el 31 de
    marzo. El período personalizado no se calcula: lo indica el usuario.
    """
    meses = MESES_POR_PERIODO.get(periodo_facturado)
    if not meses or not fecha_inicio:
        return None
    return fecha_inicio + relativedelta(months=meses) - timedelta(days=1)


@transaction.atomic
def generar_cuenta_cobro(
    *,
    cliente,
    periodo_facturado,
    fecha_inicio_periodo,
    fecha_fin_periodo,
    valor_total,
    cuenta_bancaria,
    metodo_pago,
    fecha_vencimiento_pago,
    lineas,
):
    """
    Genera la cuenta de cobro: el registro, sus líneas de servicio (en el
    orden en que se capturaron) y el PDF.

    `lineas` es una lista de diccionarios con `descripcion_linea`, `concepto`
    (opcional) y `valor_linea` (opcional). El valor total queda guardado en la
    cuenta, de modo que un cambio posterior del honorario no la afecta.
    """
    cuenta = CuentaCobro.objects.create(
        cliente=cliente,
        honorario=Honorario.objects.filter(cliente=cliente).first(),
        periodo_facturado=periodo_facturado,
        fecha_inicio_periodo=fecha_inicio_periodo,
        fecha_fin_periodo=fecha_fin_periodo,
        valor_total=valor_total,
        cuenta_bancaria=cuenta_bancaria,
        metodo_pago=metodo_pago,
        fecha_vencimiento_pago=fecha_vencimiento_pago,
    )
    CuentaCobroDetalle.objects.bulk_create(
        CuentaCobroDetalle(
            cuenta_cobro=cuenta,
            concepto=linea.get("concepto"),
            descripcion_linea=linea["descripcion_linea"],
            valor_linea=linea.get("valor_linea") or Decimal("0"),
        )
        for linea in lineas
    )
    pdf_bytes = construir_pdf_cuenta_cobro(cuenta)
    cuenta.archivo.save(f"cuenta_cobro_{cuenta.pk}.pdf", ContentFile(pdf_bytes), save=True)
    return cuenta


def _texto_periodo(cuenta):
    """Período facturado legible, por ejemplo "Trimestral (01/01/2026 a 31/03/2026)"."""
    if cuenta.fecha_inicio_periodo and cuenta.fecha_fin_periodo:
        inicio = cuenta.fecha_inicio_periodo.strftime("%d/%m/%Y")
        fin = cuenta.fecha_fin_periodo.strftime("%d/%m/%Y")
        return f"{cuenta.periodo_facturado} ({inicio} a {fin})"
    return cuenta.periodo_facturado


def _seccion_abonos_pdf(cuenta, estilos, ancho):
    """
    Pagos y abonos recibidos, con el total abonado y el saldo pendiente por
    pagar, para que el cliente vea en la cuenta lo que le falta. Si la cuenta
    no tiene abonos no se agrega nada.
    """
    abonos = list(cuenta.abonos.select_related("metodo_pago").order_by("fecha", "id_abono"))
    if not abonos:
        return []
    total_abonado = sum((abono.monto for abono in abonos), Decimal("0"))
    saldo = cuenta.valor_total - total_abonado
    filas = [["Fecha", "Medio de pago", "Valor"]]
    for abono in abonos:
        medio = escape(abono.metodo_pago.nombre_metodo) if abono.metodo_pago else "—"
        filas.append(
            [
                date_format(abono.fecha, "SHORT_DATE_FORMAT"),
                Paragraph(medio, estilos["Normal"]),
                formato_pesos(abono.monto),
            ]
        )
    filas.append(["", "Valor de la cuenta", formato_pesos(cuenta.valor_total)])
    filas.append(["", "Total abonado", formato_pesos(total_abonado)])
    filas.append(["", "SALDO PENDIENTE POR PAGAR", formato_pesos(saldo)])
    tabla = Table(filas, colWidths=[3.5 * cm, ancho - 7.5 * cm, 4 * cm])
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(paleta.TEAL)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (1, -3), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor(paleta.CREMA)),
                ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                ("ALIGN", (1, -3), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(paleta.BORDE)),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    corte = date_format(timezone.localdate())
    elementos = [
        Paragraph(f"<b>Pagos y abonos recibidos</b> (estado de cuenta al {corte})", estilos["Normal"]),
        Spacer(1, 0.2 * cm),
        tabla,
    ]
    if saldo <= 0:
        elementos.append(Spacer(1, 0.2 * cm))
        elementos.append(
            Paragraph("<b>Esta cuenta de cobro se encuentra pagada en su totalidad.</b>", estilos["Normal"])
        )
    elementos.append(Spacer(1, 0.6 * cm))
    return elementos


def actualizar_pdf_cuenta_cobro(cuenta):
    """Vuelve a generar el PDF guardado de la cuenta (por ejemplo, al registrar un abono)."""
    nombre = f"cuenta_cobro_{cuenta.pk}.pdf"
    if cuenta.archivo:
        cuenta.archivo.delete(save=False)
    cuenta.archivo.save(nombre, ContentFile(construir_pdf_cuenta_cobro(cuenta)), save=True)


def construir_pdf_cuenta_cobro(cuenta):
    """
    Arma el PDF de la cuenta de cobro con ReportLab (Platypus): membrete del
    despacho, cliente y NIT, valor, descripción del servicio por líneas,
    abonos recibidos y saldo pendiente (si los hay), período, fecha de
    vencimiento, datos bancarios y método de pago.

    Todo texto capturado por un usuario (nombres, líneas de servicio) se
    escapa antes de pasarlo a `Paragraph`, que interpreta marcado propio.
    """
    buffer = io.BytesIO()
    documento_pdf = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )
    estilos = getSampleStyleSheet()
    despacho = ConfiguracionDespacho.objects.first()
    cliente = cuenta.cliente

    elementos = encabezado_despacho(despacho, estilos, ancho_maximo=documento_pdf.width)
    elementos.append(Spacer(1, 0.8 * cm))
    elementos.append(Paragraph(f"CUENTA DE COBRO No. {cuenta.pk}", estilos["Heading2"]))
    ciudad = escape(despacho.ciudad) if despacho and despacho.ciudad else ""
    fecha = date_format(timezone.localtime(cuenta.fecha_generacion).date())
    elementos.append(Paragraph(f"{ciudad}{', ' if ciudad else ''}{fecha}", estilos["Normal"]))
    elementos.append(Spacer(1, 0.6 * cm))

    elementos.append(
        Paragraph(
            f"<b>{escape(cliente.nombre_razon_social)}</b><br/>"
            f"{escape(cliente.get_tipo_documento_display())} {escape(cliente.nit_cedula)}",
            estilos["Normal"],
        )
    )
    elementos.append(Spacer(1, 0.4 * cm))
    nombre_despacho = escape(despacho.nombre_despacho) if despacho else ""
    nit_despacho = f" NIT {escape(despacho.nit_despacho)}" if despacho and despacho.nit_despacho else ""
    elementos.append(Paragraph(f"DEBE A: <b>{nombre_despacho}</b>{nit_despacho}", estilos["Normal"]))
    elementos.append(Paragraph(f"LA SUMA DE: <b>{formato_pesos(cuenta.valor_total)}</b>", estilos["Normal"]))
    elementos.append(Spacer(1, 0.6 * cm))

    elementos.append(Paragraph("<b>Descripción del servicio</b>", estilos["Normal"]))
    elementos.append(Spacer(1, 0.2 * cm))
    filas = [["Concepto", "Valor"]]
    for linea in cuenta.detalles.all():
        valor = formato_pesos(linea.valor_linea) if linea.valor_linea else ""
        filas.append([Paragraph(escape(linea.descripcion_linea), estilos["Normal"]), valor])
    filas.append(["Total", formato_pesos(cuenta.valor_total)])
    tabla = Table(filas, colWidths=[documento_pdf.width - 4 * cm, 4 * cm])
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(paleta.TEAL)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(paleta.BORDE)),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elementos.append(tabla)
    elementos.append(Spacer(1, 0.6 * cm))
    elementos.extend(_seccion_abonos_pdf(cuenta, estilos, documento_pdf.width))

    elementos.append(Paragraph(f"<b>Período facturado:</b> {_texto_periodo(cuenta)}", estilos["Normal"]))
    elementos.append(
        Paragraph(
            f"<b>Fecha de vencimiento del pago:</b> {date_format(cuenta.fecha_vencimiento_pago)}",
            estilos["Normal"],
        )
    )
    if cuenta.metodo_pago:
        elementos.append(
            Paragraph(f"<b>Método de pago:</b> {escape(cuenta.metodo_pago.nombre_metodo)}", estilos["Normal"])
        )
    if cuenta.cuenta_bancaria:
        banco = cuenta.cuenta_bancaria
        elementos.append(Spacer(1, 0.4 * cm))
        elementos.append(
            Paragraph(
                "<b>Datos para el pago</b><br/>"
                f"{escape(banco.banco)} — Cuenta {escape(banco.tipo_cuenta)} "
                f"No. {escape(banco.numero_cuenta)}<br/>Titular: {escape(banco.titular)}",
                estilos["Normal"],
            )
        )

    documento_pdf.build(elementos)
    return buffer.getvalue()


@transaction.atomic
def eliminar_cuenta_cobro(cuenta):
    """
    Elimina una cuenta de cobro y su PDF. Una cuenta con abonos registrados
    no se elimina, para no perder la trazabilidad de la cartera.
    """
    if cuenta.abonos.exists():
        raise ValueError("No se puede eliminar una cuenta de cobro que ya tiene abonos registrados.")
    cuenta.archivo.delete(save=False)
    cuenta.delete()


# ---------------------------------------------------------------------------
# Abonos (HU016): el saldo lo calcula el disparador de PostgreSQL
# ---------------------------------------------------------------------------


def _mensaje_base_datos(error):
    """Mensaje legible que devolvió un disparador (RAISE EXCEPTION) de PostgreSQL."""
    diagnostico = getattr(error.__cause__, "diag", None)
    return getattr(diagnostico, "message_primary", None) or "La base de datos rechazó la operación."


def registrar_abono(cuenta, *, fecha, monto, metodo_pago, usuario, metodo_nuevo=""):
    """
    Registra un pago o abono. El disparador `trg_abono_calcular_saldo` fija el
    saldo anterior y el resultante (con la cuenta bloqueada) y rechaza montos
    mayores que el saldo; `trg_abono_actualizar_estado` actualiza el estado de
    pago de la cuenta. Aquí solo se traduce su rechazo en un error de negocio.

    Si se escribe un método de pago que no está en el catálogo, se agrega.
    Después se vuelve a generar el PDF de la cuenta con el abono y el saldo.
    """
    if metodo_nuevo.strip():
        metodo_pago, _ = MetodoPago.objects.get_or_create(nombre_metodo=metodo_nuevo.strip()[:40])
    try:
        with transaction.atomic():
            abono = Abono.objects.create(
                cuenta_cobro=cuenta,
                fecha=fecha,
                monto=monto,
                metodo_pago=metodo_pago,
                responsable=usuario,
                # Valores provisionales: los reemplaza el disparador antes de insertar.
                saldo_anterior=Decimal("0"),
                saldo_resultante=Decimal("0"),
            )
    except IntegrityError as error:
        raise ValueError(_mensaje_base_datos(error)) from error
    abono.refresh_from_db()
    cuenta.refresh_from_db()
    # El PDF se rehace para que el cliente vea el abono y el saldo pendiente.
    actualizar_pdf_cuenta_cobro(cuenta)
    return abono


# ---------------------------------------------------------------------------
# Envíos: individuales, masivos y programados (HU045-HU047 y ampliación)
# ---------------------------------------------------------------------------

CANALES_POR_OPCION = {CORREO: [CORREO], WHATSAPP: [WHATSAPP], AMBOS: [CORREO, WHATSAPP]}


def programar_envio(cuenta, tipo, canal, fecha_programada, usuario=None):
    """
    Programa el envío de una cuenta de cobro o de un recordatorio. Con el
    canal "Ambos" se crea un envío por correo y otro por WhatsApp. Devuelve
    la lista de envíos creados.
    """
    return [
        EnvioProgramado.objects.create(
            cuenta_cobro=cuenta,
            tipo=tipo,
            canal=canal_envio,
            fecha_programada=fecha_programada,
            usuario=usuario,
        )
        for canal_envio in CANALES_POR_OPCION[canal]
    ]


def _actualizar_estado_envio_cuenta(envio, exito):
    """Refleja en la cuenta de cobro si su envío (no un recordatorio) salió o falló."""
    if envio.tipo != EnvioProgramado.CUENTA_COBRO:
        return
    cuenta = envio.cuenta_cobro
    if exito:
        cuenta.estado_envio = CuentaCobro.ENVIADA
    elif cuenta.estado_envio != CuentaCobro.ENVIADA:
        cuenta.estado_envio = CuentaCobro.FALLIDA
    cuenta.save(update_fields=["estado_envio"])


def despachar_envio(envio, usuario=None, ahora=None):
    """
    Ejecuta un envío. El correo se envía de inmediato y queda Enviado o
    Fallido (reintentable); el de WhatsApp pasa a la bandeja de pendientes,
    porque el enlace `wa.me` necesita que una persona pulse "Enviar".
    """
    envio.fecha_procesado = ahora or timezone.now()
    if envio.canal == WHATSAPP:
        envio.estado = EnvioProgramado.PENDIENTE_WHATSAPP
        envio.save(update_fields=["estado", "fecha_procesado"])
        return envio

    reintentos = envio.comunicacion.numero_reintentos + 1 if envio.comunicacion else 0
    try:
        envios.enviar_correo(envio.cuenta_cobro, envio.tipo, hoy=timezone.localdate(envio.fecha_procesado))
        exito, detalle = True, ""
    except envios.ErrorEnvio as error:
        exito, detalle = False, str(error)[:255]
    envio.comunicacion = envios.registrar_comunicacion(
        envio.cuenta_cobro,
        CORREO,
        envio.tipo,
        usuario or envio.usuario,
        exito,
        reintentos=reintentos,
    )
    envio.estado = EnvioProgramado.ENVIADO if exito else EnvioProgramado.FALLIDO
    envio.detalle_error = detalle
    envio.save(update_fields=["estado", "fecha_procesado", "comunicacion", "detalle_error"])
    _actualizar_estado_envio_cuenta(envio, exito)
    return envio


def enviar_ahora(cuentas, tipo, canal, usuario):
    """
    Envío inmediato (individual o masivo) de cuentas de cobro o recordatorios.
    Devuelve los envíos procesados para mostrar el resumen de éxitos, fallos y
    enlaces de WhatsApp pendientes (HU046-4).
    """
    ahora = timezone.now()
    procesados = []
    for cuenta in cuentas:
        for envio in programar_envio(cuenta, tipo, canal, ahora, usuario):
            procesados.append(despachar_envio(envio, usuario=usuario, ahora=ahora))
    return procesados


def confirmar_whatsapp(envio, usuario):
    """
    Registra como enviado un WhatsApp pendiente cuando el usuario abre su
    enlace `wa.me` (con `wa.me` no existe una confirmación real de entrega).
    """
    if envio.estado != EnvioProgramado.PENDIENTE_WHATSAPP:
        raise ValueError("Este envío no está pendiente por WhatsApp.")
    enlace = envios.enlace_whatsapp(envio.cuenta_cobro, envio.tipo)
    if not enlace:
        raise ValueError("El cliente no tiene un número de celular válido para WhatsApp.")
    envio.comunicacion = envios.registrar_comunicacion(
        envio.cuenta_cobro, WHATSAPP, envio.tipo, usuario, True
    )
    envio.estado = EnvioProgramado.ENVIADO
    envio.fecha_procesado = timezone.now()
    envio.save(update_fields=["estado", "fecha_procesado", "comunicacion"])
    _actualizar_estado_envio_cuenta(envio, True)
    return enlace


def reintentar_envio(envio, usuario):
    """Vuelve a intentar un correo fallido (HU045-2)."""
    if envio.estado != EnvioProgramado.FALLIDO:
        raise ValueError("Solo se pueden reintentar los envíos fallidos.")
    return despachar_envio(envio, usuario=usuario)


def cancelar_envio(envio):
    """Cancela un envío que todavía no se ha hecho."""
    if envio.estado not in (EnvioProgramado.PROGRAMADO, EnvioProgramado.PENDIENTE_WHATSAPP):
        raise ValueError("Solo se pueden cancelar envíos programados o pendientes.")
    envio.estado = EnvioProgramado.CANCELADO
    envio.save(update_fields=["estado"])


# ---------------------------------------------------------------------------
# Proceso automático de cobro (comando `procesar_cobros`)
# ---------------------------------------------------------------------------


def marcar_cuentas_vencidas(hoy):
    """Pasa a "Vencida" las cuentas con saldo pendiente cuya fecha de pago ya pasó."""
    marcadas = 0
    candidatas = CuentaCobro.objects.filter(fecha_vencimiento_pago__lt=hoy).exclude(
        estado_pago__in=[CuentaCobro.PAGADA, CuentaCobro.VENCIDA]
    )
    for cuenta in candidatas:
        if cuenta.saldo_pendiente > 0:
            cuenta.estado_pago = CuentaCobro.VENCIDA
            cuenta.save(update_fields=["estado_pago"])
            marcadas += 1
    return marcadas


def generar_cobros_mensuales(configuracion, ahora):
    """
    Cobro mensual automático: desde el día configurado, genera la cuenta de
    cobro del mes de cada cliente activo con honorario, una sola vez por mes,
    y programa su envío inmediato por el canal configurado.
    """
    hoy = timezone.localdate(ahora)
    if not configuracion.cobro_automatico_activo or hoy.day < configuracion.dia_generacion:
        return []
    inicio = hoy.replace(day=1)
    clientes = Cliente.objects.filter(estado=Cliente.ACTIVO, honorario__monto__gt=0).order_by(
        "nombre_razon_social"
    )
    generadas = []
    for cliente in clientes:
        ya_generada = CuentaCobro.objects.filter(
            cliente=cliente, periodo_facturado=CuentaCobro.MENSUAL, fecha_inicio_periodo=inicio
        ).exists()
        if ya_generada:
            continue
        sugerencia = selectores.sugerencia_cuenta_cobro(cliente)
        lineas = sugerencia["lineas"] or [
            {"descripcion_linea": f"Honorarios contables {date_format(inicio, 'F Y')}", "valor_linea": None}
        ]
        cuenta = generar_cuenta_cobro(
            cliente=cliente,
            periodo_facturado=CuentaCobro.MENSUAL,
            fecha_inicio_periodo=inicio,
            fecha_fin_periodo=calcular_fin_periodo(CuentaCobro.MENSUAL, inicio),
            valor_total=sugerencia["valor_total"],
            cuenta_bancaria=configuracion.cuenta_bancaria,
            metodo_pago=configuracion.metodo_pago,
            fecha_vencimiento_pago=hoy + timedelta(days=configuracion.dias_plazo_pago),
            lineas=lineas,
        )
        programar_envio(cuenta, EnvioProgramado.CUENTA_COBRO, configuracion.canal_cobro, ahora)
        generadas.append(cuenta)
    return generadas


def programar_recordatorios_automaticos(configuracion, ahora):
    """
    Recordatorios automáticos: uno cuando faltan los días configurados para
    el vencimiento, y luego uno cada `frecuencia_mora_dias` mientras la cuenta
    siga en mora. No se repite si ya hubo un recordatorio en ese intervalo.
    """
    if not configuracion.recordatorios_activos:
        return []
    hoy = timezone.localdate(ahora)
    programados = []
    for cuenta in CuentaCobro.objects.exclude(estado_pago=CuentaCobro.PAGADA).select_related("cliente"):
        if cuenta.saldo_pendiente <= 0:
            continue
        dias_para_vencer = (cuenta.fecha_vencimiento_pago - hoy).days
        if 0 <= dias_para_vencer <= configuracion.dias_antes_vencimiento:
            desde = cuenta.fecha_vencimiento_pago - timedelta(days=configuracion.dias_antes_vencimiento)
        elif dias_para_vencer < 0:
            desde = hoy - timedelta(days=configuracion.frecuencia_mora_dias - 1)
        else:
            continue
        ya_recordada = (
            cuenta.envios_programados.filter(
                tipo=EnvioProgramado.RECORDATORIO, fecha_programada__date__gte=desde
            )
            .exclude(estado=EnvioProgramado.CANCELADO)
            .exists()
        )
        if not ya_recordada:
            programados += programar_envio(
                cuenta, EnvioProgramado.RECORDATORIO, configuracion.canal_recordatorio, ahora
            )
    return programados


def despachar_programados(ahora):
    """Ejecuta los envíos programados cuya hora ya llegó."""
    pendientes = EnvioProgramado.objects.filter(
        estado=EnvioProgramado.PROGRAMADO, fecha_programada__lte=ahora
    ).select_related("cuenta_cobro__cliente", "comunicacion", "usuario")
    return [despachar_envio(envio, ahora=ahora) for envio in pendientes]


def procesar_cobros(ahora=None):
    """
    Proceso automático completo (cron cada 15 minutos o botón "Ejecutar
    ahora"): marca vencidas, genera el cobro mensual, programa recordatorios
    y despacha los envíos cuya hora llegó. Es idempotente: correrlo varias
    veces seguidas no duplica cuentas ni recordatorios. Devuelve un resumen.
    """
    ahora = ahora or timezone.now()
    configuracion = ConfiguracionCobro.obtener()
    vencidas = marcar_cuentas_vencidas(timezone.localdate(ahora))
    generadas = generar_cobros_mensuales(configuracion, ahora)
    recordatorios = programar_recordatorios_automaticos(configuracion, ahora)
    despachados = despachar_programados(ahora)
    configuracion.ultima_ejecucion = ahora
    configuracion.save(update_fields=["ultima_ejecucion"])
    return {
        "cuentas_vencidas": vencidas,
        "cuentas_generadas": len(generadas),
        "recordatorios_programados": len(recordatorios),
        "correos_enviados": sum(1 for e in despachados if e.estado == EnvioProgramado.ENVIADO),
        "correos_fallidos": sum(1 for e in despachados if e.estado == EnvioProgramado.FALLIDO),
        "whatsapp_pendientes": sum(1 for e in despachados if e.estado == EnvioProgramado.PENDIENTE_WHATSAPP),
    }
