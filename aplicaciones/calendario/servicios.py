"""
Reglas de negocio del módulo 2: cálculo DIAN, vencimientos, alertas y anotaciones.

Las vistas delegan en estas funciones la escritura en los modelos, para que
las operaciones que tocan varias tablas queden dentro de una transacción.
"""

from django.core.exceptions import PermissionDenied
from django.db import transaction

from aplicaciones.clientes.models import Cliente

from .models import (
    AnotacionCalendario,
    AnotacionCalendarioDestinatario,
    TablaReferenciaDian,
    Vencimiento,
)

# Tipos de documento con cálculo automático de grupo DIAN.
DOCUMENTOS_CON_CALCULO = (Cliente.NIT, Cliente.CC)

# Obligaciones que aplican según el régimen tributario del cliente.
REGIMEN_SIMPLE = "Régimen simple de tributación"
REGIMEN_ORDINARIO = "Régimen ordinario"


def calcular_grupo_nit(cliente):
    """
    Calcula el grupo DIAN del cliente para buscar en la tabla de referencia.

    - Empresas (NIT): último dígito del NIT ("0" a "9").
    - Personas naturales (CC): últimos dos dígitos de la cédula ("00" a "99").
    - Otros documentos (CE, TI, pasaporte, RUT): no hay cálculo automático;
      sus vencimientos se registran de forma manual.

    Args:
        cliente: instancia de Cliente.

    Returns:
        str | None: grupo DIAN o None si no aplica cálculo automático.
    """
    numero = (cliente.nit_cedula or "").strip()
    if not numero.isdigit():
        return None
    if cliente.tipo_documento == Cliente.NIT:
        return numero[-1]
    if cliente.tipo_documento == Cliente.CC:
        return numero[-2:].zfill(2)
    return None


def obligaciones_por_cliente(cliente):
    """
    Determina las obligaciones nacionales DIAN que aplican al cliente.

    Reglas según régimen tributario y responsabilidad de IVA:

    - Régimen simple: "RST anticipo bimestral" y "RST consolidada anual".
    - Régimen ordinario jurídico: "Renta personas jurídicas" y
      "Retención en la fuente"; si es responsable de IVA, "IVA bimestral".
    - Régimen ordinario natural: "Renta personas naturales"; si es
      responsable de IVA, "IVA bimestral" y "Retención en la fuente".
    - Otros regímenes: solo IVA bimestral si es responsable de IVA.

    Args:
        cliente: instancia de Cliente.

    Returns:
        list[str]: tipos de obligación que le corresponden al cliente. La
            generación de vencimientos solo crea las que existan en la tabla
            de referencia DIAN cargada por el Administrador.
    """
    regimen = (cliente.regimen_tributario or "").strip().lower()

    if "simple" in regimen or "simplif" in regimen:
        return ["RST anticipo bimestral", "RST consolidada anual"]
    if cliente.tipo_persona == Cliente.JURIDICA:
        obligaciones = ["Renta personas jurídicas", "Retención en la fuente"]
        if cliente.responsable_iva:
            obligaciones.append("IVA bimestral")
        return obligaciones

    obligaciones = ["Renta personas naturales"]
    if cliente.responsable_iva:
        obligaciones += ["IVA bimestral", "Retención en la fuente"]
    return obligaciones


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
        dict: resumen con cantidad de vencimientos creados y omitidos.
    """
    grupo = calcular_grupo_nit(cliente)
    resumen = {"creados": 0, "omitidos": 0, "sin_grupo": grupo is None}
    if grupo is None:
        return resumen

    responsable = cliente.responsable or usuario
    referencias = TablaReferenciaDian.objects.filter(
        tipo_obligacion__in=obligaciones_por_cliente(cliente),
        grupo_nit=grupo,
    )

    for referencia in referencias:
        _, creado = Vencimiento.objects.get_or_create(
            cliente=cliente,
            tipo_obligacion=referencia.tipo_obligacion,
            ambito=Vencimiento.NACIONAL,
            fecha_vencimiento=referencia.fecha_vencimiento,
            tarea=None,
            defaults={
                "responsable": responsable,
                "estado_validacion": Vencimiento.PENDIENTE_VALIDAR,
            },
        )
        if creado:
            resumen["creados"] += 1
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
        dict: totales de clientes procesados, vencimientos creados y omitidos.
    """
    clientes = Cliente.objects.all()
    if solo_activos:
        clientes = clientes.filter(estado=Cliente.ACTIVO)

    total = {"clientes": 0, "creados": 0, "omitidos": 0, "sin_grupo": 0}
    for cliente in clientes:
        resumen = generar_vencimientos_cliente(cliente, usuario)
        total["clientes"] += 1
        total["creados"] += resumen["creados"]
        total["omitidos"] += resumen["omitidos"]
        total["sin_grupo"] += 1 if resumen["sin_grupo"] else 0
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
