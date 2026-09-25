"""
Canales de envío del módulo 6: correo electrónico y WhatsApp.

- Correo: `EmailMessage` de Django con el PDF de la cuenta de cobro adjunto.
  Usa el backend configurado (SMTP con las variables `CORREO_*` del `.env`;
  en desarrollo, la consola de `runserver`).
- WhatsApp: enlace `https://wa.me/<número>?text=<mensaje>` (decisión T2). No
  permite envío automático: una persona abre el enlace y pulsa "Enviar". El
  mensaje lleva un enlace público firmado al PDF, porque `wa.me` no adjunta
  archivos.

Cada envío queda registrado en `comunicaciones.Comunicacion` (Módulo 7).
"""

import re
from urllib.parse import quote

from django.conf import settings
from django.core import signing
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from aplicaciones.comunicaciones.models import Comunicacion
from aplicaciones.seguridad.models import ConfiguracionDespacho

from .models import CORREO, WHATSAPP, CuentaCobro, EnvioProgramado
from .templatetags.finanzas_tags import formato_pesos

MODULO_ORIGEN = "Honorarios"
SAL_PDF_PUBLICO = "finanzas.pdf_publico"
VIGENCIA_ENLACE_PDF = 60 * 60 * 24 * 30  # 30 días, en segundos


class ErrorEnvio(Exception):
    """Un envío no se pudo realizar (sin destinatario, error del servidor de correo, etc.)."""


# ---------------------------------------------------------------------------
# Enlace público firmado al PDF (para WhatsApp)
# ---------------------------------------------------------------------------


def token_pdf_publico(cuenta):
    """Token firmado e infalsificable con el id de la cuenta; vence en 30 días."""
    return signing.TimestampSigner(salt=SAL_PDF_PUBLICO).sign(str(cuenta.pk))


def cuenta_desde_token(token):
    """Cuenta de cobro del token, o None si el token fue alterado o ya venció."""
    try:
        pk = signing.TimestampSigner(salt=SAL_PDF_PUBLICO).unsign(token, max_age=VIGENCIA_ENLACE_PDF)
    except signing.BadSignature:
        return None
    return CuentaCobro.objects.filter(pk=pk).first()


def enlace_pdf_publico(cuenta):
    """URL absoluta del PDF para compartir con el cliente (requiere `URL_SITIO` público en producción)."""
    ruta = reverse("finanzas:pdf_publico", args=[token_pdf_publico(cuenta)])
    return f"{settings.URL_SITIO.rstrip('/')}{ruta}"


# ---------------------------------------------------------------------------
# Contenido de los mensajes
# ---------------------------------------------------------------------------


def _contexto_mensaje(cuenta, hoy=None):
    """Datos del mensaje; `hoy` es la fecha del envío (la del proceso automático, si aplica)."""
    despacho = ConfiguracionDespacho.objects.first()
    saldo = cuenta.saldo_pendiente
    return {
        "cuenta": cuenta,
        "cliente": cuenta.cliente,
        "nombre_despacho": despacho.nombre_despacho if despacho else "",
        "valor_total": formato_pesos(cuenta.valor_total),
        "saldo_pendiente": formato_pesos(saldo),
        "fecha_vencimiento": date_format(cuenta.fecha_vencimiento_pago),
        "en_mora": saldo > 0 and cuenta.fecha_vencimiento_pago < (hoy or timezone.localdate()),
        "cuenta_bancaria": cuenta.cuenta_bancaria,
        "metodo_pago": cuenta.metodo_pago,
        "enlace_pdf": enlace_pdf_publico(cuenta),
    }


def asunto_correo(cuenta, tipo):
    if tipo == EnvioProgramado.RECORDATORIO:
        return f"Recordatorio de pago - Cuenta de cobro No. {cuenta.pk}"
    return f"Cuenta de cobro No. {cuenta.pk} - {cuenta.cliente.nombre_razon_social}"


def texto_mensaje(cuenta, tipo, canal, hoy=None):
    """Texto del correo o del WhatsApp según el tipo de envío (cuenta de cobro o recordatorio)."""
    nombre = "recordatorio" if tipo == EnvioProgramado.RECORDATORIO else "cuenta_cobro"
    sufijo = "whatsapp" if canal == WHATSAPP else "correo"
    plantilla = f"finanzas/mensajes/{nombre}_{sufijo}.txt"
    return render_to_string(plantilla, _contexto_mensaje(cuenta, hoy)).strip()


# ---------------------------------------------------------------------------
# Registro en Comunicaciones
# ---------------------------------------------------------------------------


def registrar_comunicacion(cuenta, canal, tipo, usuario, exito, automatico=False, reintentos=0):
    """Deja la traza del envío en el historial de comunicaciones del cliente (HU045-3)."""
    return Comunicacion.objects.create(
        cliente=cuenta.cliente,
        canal=canal,
        tipo=Comunicacion.AUTOMATICA if automatico else Comunicacion.MANUAL,
        contenido_resumen=f"{tipo} No. {cuenta.pk} por {formato_pesos(cuenta.saldo_pendiente)}",
        usuario=usuario,
        estado_envio=Comunicacion.EXITO if exito else Comunicacion.FALLO,
        numero_reintentos=reintentos,
        modulo_origen=MODULO_ORIGEN,
    )


# ---------------------------------------------------------------------------
# Canales
# ---------------------------------------------------------------------------


def enviar_correo(cuenta, tipo, hoy=None):
    """
    Envía la cuenta de cobro (con el PDF adjunto) o el recordatorio al correo
    del cliente. Lanza `ErrorEnvio` si no hay destinatario o si el servidor de
    correo rechaza el envío.
    """
    destinatario = cuenta.cliente.correo_cliente
    if not destinatario:
        raise ErrorEnvio("El cliente no tiene correo registrado.")
    despacho = ConfiguracionDespacho.objects.first()
    mensaje = EmailMessage(
        subject=asunto_correo(cuenta, tipo),
        body=texto_mensaje(cuenta, tipo, CORREO, hoy),
        to=[destinatario],
        reply_to=[despacho.correo] if despacho and despacho.correo else None,
    )
    if cuenta.archivo:
        with cuenta.archivo.open("rb") as archivo:
            mensaje.attach(f"cuenta_cobro_{cuenta.pk}.pdf", archivo.read(), "application/pdf")
    try:
        mensaje.send(fail_silently=False)
    except Exception as error:  # SMTP, red o configuración: se reporta como fallo reintentable
        raise ErrorEnvio(f"No se pudo enviar el correo: {error}") from error


def numero_whatsapp(cliente):
    """
    Número en formato internacional para `wa.me`, tomado del contacto del
    cliente: se conservan solo los dígitos y a un celular colombiano de 10
    dígitos (empieza por 3) se le antepone el indicativo 57. None si no hay
    un número utilizable.
    """
    digitos = re.sub(r"\D", "", cliente.informacion_contacto or "")
    if len(digitos) == 10 and digitos.startswith("3"):
        return f"57{digitos}"
    if len(digitos) == 12 and digitos.startswith("573"):
        return digitos
    return None


def enlace_whatsapp(cuenta, tipo):
    """Enlace `wa.me` con el mensaje ya escrito, o None si el cliente no tiene celular válido."""
    numero = numero_whatsapp(cuenta.cliente)
    if not numero:
        return None
    texto = texto_mensaje(cuenta, tipo, WHATSAPP)
    return f"https://wa.me/{numero}?text={quote(texto)}"
