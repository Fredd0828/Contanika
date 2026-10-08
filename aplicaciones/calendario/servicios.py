"""
Reglas de negocio del módulo 2: cálculo DIAN, vencimientos, alertas y anotaciones.

Las vistas delegan en estas funciones la escritura en los modelos, para que
las operaciones que tocan varias tablas queden dentro de una transacción.
"""

import logging
import re
from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from aplicaciones.clientes.models import Cliente
from aplicaciones.comunicaciones.models import Comunicacion

from . import selectores
from .models import (
    AnotacionCalendario,
    AnotacionCalendarioDestinatario,
    ConfiguracionAlerta,
    TablaReferenciaDian,
    Vencimiento,
)

logger = logging.getLogger(__name__)

# Valor de `comunicacion.modulo_origen` para las alertas enviadas por correo.
MODULO_ORIGEN_ALERTAS = "Calendario"

# Tipos de documento con cálculo automático de grupo DIAN.
DOCUMENTOS_CON_CALCULO = (Cliente.NIT, Cliente.CC)


def calcular_grupos_dian(cliente):
    """
    Calcula los grupos DIAN del cliente para buscar en la tabla de referencia.

    El grupo depende de la obligación, no del tipo de documento: la DIAN
    ordena unas por el último dígito del documento (IVA, retención en la
    fuente, renta de personas jurídicas, RST) y otras por los dos últimos
    (renta de personas naturales). Por eso se devuelven ambos y la búsqueda
    se queda con el que existe para cada obligación. Así una persona natural
    registrada con NIT o con cédula calcula igual su renta, su IVA y su
    retención.

    Los documentos que no son NIT ni cédula (CE, TI, pasaporte, RUT) o que
    no son numéricos no tienen cálculo automático: sus vencimientos se
    registran de forma manual.

    Args:
        cliente: instancia de Cliente.

    Returns:
        list[str]: [último dígito, dos últimos dígitos] o lista vacía si no
            aplica cálculo automático.
    """
    numero = (cliente.nit_cedula or "").strip()
    if cliente.tipo_documento not in DOCUMENTOS_CON_CALCULO or not numero.isdigit():
        return []
    return [numero[-1], numero[-2:].zfill(2)]


def obligaciones_por_cliente(cliente):
    """
    Devuelve las obligaciones tributarias que el usuario marcó para el cliente.

    Las obligaciones ya no se adivinan por régimen tributario ni por
    responsabilidad de IVA: se eligen explícitamente en el perfil del
    cliente (Módulo 1), lo que permite marcar cosas como "Exógena nacional"
    o "Exógena distrital" que no se pueden inferir de un texto libre.

    Args:
        cliente: instancia de Cliente.

    Returns:
        list[str]: tipos de obligación marcados para el cliente. La
            generación de vencimientos solo crea las que existan en la tabla
            de referencia DIAN cargada por el Administrador.
    """
    return list(cliente.obligaciones.values_list("obligacion_tributaria__nombre", flat=True))


@transaction.atomic
def generar_vencimientos_cliente(cliente, usuario):
    """
    Genera los vencimientos nacionales del cliente desde la tabla DIAN.

    Para cada obligación que aplica, crea un vencimiento por cada período
    cargado en la tabla de referencia que aún no exista para el cliente.
    Los vencimientos automáticos quedan "Pendiente de validar" para que el
    contador los revise; la fecha queda editable (regla transversal).

    Args:
        cliente: instancia de Cliente.
        usuario: usuario que dispara el cálculo (queda como responsable si
            el cliente no tiene uno asignado).

    Returns:
        dict: resumen con cantidad de vencimientos creados, actualizados
            (la fecha cambió porque el Administrador corrigió la tabla DIAN
            y se recalculó) y omitidos (sin cambios), `sin_coincidencia` con
            las obligaciones que tienen fechas cargadas pero ninguna para el
            documento del cliente, y `sin_referencia` con
            las obligaciones marcadas en el cliente que no generaron nada
            porque la tabla DIAN no tiene ninguna fecha cargada para ellas
            (p. ej. una obligación recién agregada al catálogo que el
            Administrador todavía no cargó).
    """
    obligaciones = obligaciones_por_cliente(cliente)
    grupos = calcular_grupos_dian(cliente)
    resumen = {
        "creados": 0,
        "actualizados": 0,
        "omitidos": 0,
        "sin_grupo": not grupos,
        "sin_referencia": [],
        "sin_coincidencia": [],
    }
    if not grupos:
        return resumen

    tipos_con_referencia = set(
        TablaReferenciaDian.objects.filter(tipo_obligacion__in=obligaciones)
        .values_list("tipo_obligacion", flat=True)
        .distinct()
    )
    resumen["sin_referencia"] = [
        obligacion for obligacion in obligaciones if obligacion not in tipos_con_referencia
    ]

    responsable = cliente.responsable or usuario
    referencias = TablaReferenciaDian.objects.filter(
        tipo_obligacion__in=obligaciones,
        grupo_nit__in=grupos,
    )
    # Obligaciones con fechas cargadas pero ninguna para el documento del
    # cliente (p. ej. renta de personas jurídicas marcada a una persona natural).
    con_coincidencia = set(referencias.values_list("tipo_obligacion", flat=True).distinct())
    resumen["sin_coincidencia"] = [
        obligacion
        for obligacion in obligaciones
        if obligacion in tipos_con_referencia and obligacion not in con_coincidencia
    ]

    for referencia in referencias:
        vencimiento, creado = Vencimiento.objects.get_or_create(
            cliente=cliente,
            tipo_obligacion=referencia.tipo_obligacion,
            ambito=Vencimiento.NACIONAL,
            periodo_gravable=referencia.periodo_gravable,
            tarea=None,
            defaults={
                "fecha_vencimiento": referencia.fecha_vencimiento,
                "responsable": responsable,
                "estado_validacion": Vencimiento.PENDIENTE_VALIDAR,
            },
        )
        if creado:
            resumen["creados"] += 1
        elif (
            vencimiento.fecha_vencimiento != referencia.fecha_vencimiento
            and vencimiento.estado_validacion != Vencimiento.VALIDADO
        ):
            # Un vencimiento ya validado (o corregido a mano) no se pisa al recalcular.
            vencimiento.fecha_vencimiento = referencia.fecha_vencimiento
            vencimiento.estado_validacion = Vencimiento.PENDIENTE_VALIDAR
            vencimiento.save(update_fields=["fecha_vencimiento", "estado_validacion"])
            resumen["actualizados"] += 1
        else:
            resumen["omitidos"] += 1
    return resumen


@transaction.atomic
def generar_vencimientos_masivo(usuario, solo_activos=True):
    """
    Genera los vencimientos DIAN de todos los clientes del despacho.

    Args:
        usuario: usuario que dispara el cálculo masivo.
        solo_activos: si es True, omite clientes inactivos.

    Returns:
        dict: totales de clientes procesados, vencimientos creados,
            actualizados (fecha corregida al recalcular) y omitidos, y
            `sin_referencia` con el conjunto (sin duplicados) de
            obligaciones que no generaron nada en ningún cliente por falta
            de fechas cargadas en la tabla DIAN.
    """
    clientes = Cliente.objects.all()
    if solo_activos:
        clientes = clientes.filter(estado=Cliente.ACTIVO)

    total = {
        "clientes": 0,
        "creados": 0,
        "actualizados": 0,
        "omitidos": 0,
        "sin_grupo": 0,
        "sin_referencia": set(),
    }
    for cliente in clientes:
        resumen = generar_vencimientos_cliente(cliente, usuario)
        total["clientes"] += 1
        total["creados"] += resumen["creados"]
        total["actualizados"] += resumen["actualizados"]
        total["omitidos"] += resumen["omitidos"]
        total["sin_grupo"] += 1 if resumen["sin_grupo"] else 0
        total["sin_referencia"].update(resumen["sin_referencia"])
    total["sin_referencia"] = sorted(total["sin_referencia"])
    return total


@transaction.atomic
def guardar_vencimiento_manual(formulario, usuario):
    """
    Guarda un vencimiento registrado manualmente (distrital, municipal u otro).

    Args:
        formulario: VencimientoManualForm ya validado.
        usuario: usuario que registra el vencimiento.

    Returns:
        Vencimiento: el vencimiento guardado.
    """
    vencimiento = formulario.save(commit=False)
    if not vencimiento.responsable_id:
        vencimiento.responsable = usuario
    vencimiento.estado_validacion = ""
    vencimiento.save()
    return vencimiento


@transaction.atomic
def guardar_vencimiento_editado(formulario):
    """
    Guarda los cambios de un vencimiento existente.

    Si el contador cambia la fecha de un vencimiento automático DIAN, queda
    "Validado": ya lo revisó y lo corrigió a su criterio, y volver a calcular
    el cliente no debe pisarle esa fecha.

    Args:
        formulario: VencimientoManualForm ya validado, con la instancia a editar.

    Returns:
        Vencimiento: el vencimiento guardado.
    """
    vencimiento = formulario.instance
    era_automatico = vencimiento.es_automatico_dian
    vencimiento = formulario.save(commit=False)
    if era_automatico and "fecha_vencimiento" in formulario.changed_data:
        vencimiento.estado_validacion = Vencimiento.VALIDADO
    vencimiento.save()
    formulario.save_m2m()
    return vencimiento


@transaction.atomic
def validar_vencimiento(vencimiento, validado=True):
    """
    Marca un vencimiento automático DIAN como validado o pendiente.

    Args:
        vencimiento: instancia de Vencimiento.
        validado: True para validar, False para devolver a pendiente.

    Returns:
        Vencimiento: el vencimiento actualizado.
    """
    vencimiento.estado_validacion = Vencimiento.VALIDADO if validado else Vencimiento.PENDIENTE_VALIDAR
    vencimiento.save(update_fields=["estado_validacion"])
    return vencimiento


def puede_actualizar_estado(usuario, vencimiento):
    """
    Indica si el usuario puede cambiar el estado de presentación del vencimiento.

    Administrador y Contador Senior, cualquiera. El Contador Junior ve todo el
    calendario, pero solo marca el avance de los vencimientos de los clientes
    que tiene a su cargo o que tiene asignados como responsable.
    """
    if not usuario.es_contador_junior:
        return True
    return usuario.id_usuario in (vencimiento.cliente.responsable_id, vencimiento.responsable_id)


@transaction.atomic
def cambiar_estado_presentacion(vencimiento, nuevo_estado):
    """
    Actualiza el estado de presentación de un vencimiento.

    Args:
        vencimiento: instancia de Vencimiento.
        nuevo_estado: uno de Vencimiento.OPCIONES_ESTADO_PRESENTACION.

    Returns:
        Vencimiento: el vencimiento actualizado.
    """
    estados_validos = {opcion[0] for opcion in Vencimiento.OPCIONES_ESTADO_PRESENTACION}
    if nuevo_estado not in estados_validos:
        raise ValueError(f"Estado de presentación no válido: {nuevo_estado}")
    vencimiento.estado_presentacion = nuevo_estado
    vencimiento.save(update_fields=["estado_presentacion"])
    return vencimiento


@transaction.atomic
def guardar_alerta(formulario, vencimiento):
    """
    Guarda una alerta configurada para un vencimiento.

    Args:
        formulario: ConfiguracionAlertaForm ya validado.
        vencimiento: vencimiento al que pertenece la alerta.

    Returns:
        ConfiguracionAlerta: la alerta guardada.
    """
    alerta = formulario.save(commit=False)
    alerta.vencimiento = vencimiento
    alerta.save()
    return alerta


@transaction.atomic
def eliminar_alerta(alerta):
    """Elimina una configuración de alerta (operación irreversible)."""
    alerta.delete()
    return True


@transaction.atomic
def guardar_anotacion(formulario, usuario, destinatarios=None):
    """
    Guarda una anotación del calendario y, si aplica, sus destinatarios.

    Args:
        formulario: AnotacionCalendarioForm ya validado.
        usuario: autor de la anotación.
        destinatarios: lista de usuarios etiquetados (solo cuando la
            visibilidad es "Por etiqueta").

    Returns:
        AnotacionCalendario: la anotación guardada.
    """
    anotacion = formulario.save(commit=False)
    anotacion.autor = usuario
    anotacion.save()

    if anotacion.visibilidad == AnotacionCalendario.POR_ETIQUETA and destinatarios:
        for destinatario in destinatarios:
            AnotacionCalendarioDestinatario.objects.get_or_create(
                anotacion_calendario=anotacion,
                usuario=destinatario,
            )
    return anotacion


@transaction.atomic
def eliminar_anotacion(anotacion, usuario):
    """
    Elimina una anotación si el usuario tiene permiso sobre ella.

    Solo el autor o un administrador pueden eliminar la anotación.
    """
    if anotacion.autor_id != usuario.id_usuario and not usuario.es_administrador:
        raise PermissionDenied("Solo el autor o un administrador pueden eliminar la anotación.")
    anotacion.delete()
    return True


# ---------------------------------------------------------------------------
# Alertas automáticas (HU040)
# ---------------------------------------------------------------------------


def destinatario_alerta(vencimiento):
    """Responsable asignado al vencimiento o, si no tiene, el responsable del cliente (HU040-3)."""
    return vencimiento.responsable or vencimiento.cliente.responsable


def texto_alerta(vencimiento, hoy=None):
    """Mensaje de la alerta: qué vence, de quién, cuándo y cuántos días faltan."""
    hoy = hoy or timezone.localdate()
    dias = (vencimiento.fecha_vencimiento - hoy).days
    cuando = "vence hoy" if dias == 0 else f"vence en {dias} día{'s' if dias != 1 else ''}"
    fecha = date_format(vencimiento.fecha_vencimiento, "j \\d\\e F \\d\\e Y")
    return f"{vencimiento.tipo_obligacion} de {vencimiento.cliente.nombre_razon_social} {cuando} ({fecha})."


def enlace_vencimiento(vencimiento):
    """URL absoluta del detalle del vencimiento, para los mensajes."""
    ruta = reverse("calendario:detalle", args=[vencimiento.pk])
    return f"{settings.URL_SITIO.rstrip('/')}{ruta}"


def enlace_whatsapp_alerta(vencimiento, usuario, hoy=None):
    """
    Enlace `wa.me` con la alerta para el celular del responsable, o None si no
    tiene uno utilizable. Como en el Módulo 6 (decisión T2), `wa.me` no envía
    solo: una persona abre el enlace y pulsa "Enviar".
    """
    digitos = re.sub(r"\D", "", usuario.telefono or "")
    if len(digitos) == 10 and digitos.startswith("3"):
        digitos = f"57{digitos}"
    if not (len(digitos) == 12 and digitos.startswith("573")):
        return None
    texto = f"{texto_alerta(vencimiento, hoy)} {enlace_vencimiento(vencimiento)}"
    return f"https://wa.me/{digitos}?text={quote(texto)}"


def _registrar_comunicacion_alerta(alerta, destinatario, exito):
    """Deja la alerta enviada en el historial de comunicaciones del cliente (Módulo 7)."""
    vencimiento = alerta.vencimiento
    return Comunicacion.objects.create(
        cliente=vencimiento.cliente,
        canal=Comunicacion.CORREO,
        tipo=Comunicacion.AUTOMATICA,
        contenido_resumen=f"Alerta a {destinatario.nombre}: {texto_alerta(vencimiento)}",
        usuario=destinatario,
        estado_envio=Comunicacion.EXITO if exito else Comunicacion.FALLO,
        modulo_origen=MODULO_ORIGEN_ALERTAS,
    )


def _enviar_alerta_por_correo(alerta, hoy):
    """Envía la alerta al correo del responsable. Devuelve True si salió."""
    vencimiento = alerta.vencimiento
    destinatario = destinatario_alerta(vencimiento)
    if destinatario is None or not destinatario.correo:
        return False
    cuerpo = (
        f"Hola {destinatario.nombre},\n\n"
        f"{texto_alerta(vencimiento, hoy)}\n\n"
        f"Responsable: {destinatario.nombre}\n"
        f"Ver el vencimiento: {enlace_vencimiento(vencimiento)}\n"
    )
    asunto = (
        f"Alerta de vencimiento: {vencimiento.tipo_obligacion} - {vencimiento.cliente.nombre_razon_social}"
    )
    try:
        send_mail(asunto, cuerpo, None, [destinatario.correo], fail_silently=False)
    except Exception:  # SMTP, red o configuración: se reintenta en la próxima corrida
        logger.exception("No se pudo enviar la alerta %s por correo", alerta.pk)
        return False
    _registrar_comunicacion_alerta(alerta, destinatario, exito=True)
    return True


def procesar_alertas(hoy=None):
    """
    Envía las alertas del Calendario cuyo aviso ya llegó (HU040).

    Pensado para el cron (`procesar_alertas`). Para cada alerta en curso que
    aún no se haya enviado para la fecha actual del vencimiento:
    - Correo: lo envía al responsable y registra la comunicación; si falla,
      queda sin marcar y se reintenta en la próxima corrida.
    - Notificación interna: queda registrada como enviada (la campana la
      muestra mientras el vencimiento siga pendiente).
    - WhatsApp: no se marca; el enlace `wa.me` aparece en la campana y una
      persona lo envía.
    Es idempotente: `fecha_envio` evita repetir el aviso.

    Returns:
        dict: contadores de correos enviados, fallidos o sin destinatario y
            notificaciones internas registradas.
    """
    hoy = hoy or timezone.localdate()
    resumen = {"correos_enviados": 0, "correos_fallidos": 0, "notificaciones": 0}
    for alerta in selectores.alertas_en_curso(hoy=hoy):
        if alerta.fecha_envio and alerta.fecha_envio >= alerta.fecha_aviso:
            continue
        if alerta.canal == ConfiguracionAlerta.CORREO:
            if not _enviar_alerta_por_correo(alerta, hoy):
                resumen["correos_fallidos"] += 1
                continue
            resumen["correos_enviados"] += 1
        elif alerta.canal == ConfiguracionAlerta.NOTIFICACION:
            resumen["notificaciones"] += 1
        else:
            continue
        alerta.fecha_envio = hoy
        alerta.save(update_fields=["fecha_envio"])
    return resumen
