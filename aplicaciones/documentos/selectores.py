"""
Consultas reutilizables del módulo 4: expedición de documentos y certificados.

Se separan de las vistas para reutilizarse en el panel de generación, el
histórico, el panel de la ficha del cliente y la construcción del PDF, que
comparten la misma forma de armar el contexto de una plantilla renderizada.
"""

from django.template import Context, Template
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from aplicaciones.clientes.models import Cliente
from aplicaciones.seguridad.models import ConfiguracionDespacho, Rol, Usuario

from .models import CampoPlantilla, Documento, Plantilla


def clave_variable_campo(nombre_campo):
    """Convierte el nombre de un campo en la clave usada como variable de plantilla."""
    return slugify(nombre_campo).replace("-", "_")


def plantillas_activas():
    """Plantillas disponibles para el selector del panel de generación."""
    return Plantilla.objects.all()


def campos_simples(plantilla):
    """Campos de tipo Simple propios de una plantilla, en orden de creación."""
    return plantilla.campos.filter(tipo_campo=CampoPlantilla.SIMPLE)


def campos_repetibles(plantilla):
    """Campos de tipo Repetible propios de una plantilla, en orden de creación."""
    return plantilla.campos.filter(tipo_campo=CampoPlantilla.REPETIBLE)


def clientes_para_generar(usuario):
    """
    Clientes activos disponibles para generar un documento.

    El Contador Junior solo puede generar documentos para los clientes que
    tiene asignados como responsable.
    """
    consulta = Cliente.objects.filter(estado=Cliente.ACTIVO)
    if usuario.es_contador_junior:
        consulta = consulta.filter(responsable=usuario)
    return consulta


def firmantes_disponibles():
    """
    Usuarios que pueden prestar su firma para un documento generado.

    Solo Administrador y Contador Senior guardan firma (RQF del módulo 4);
    el Contador Junior nunca aparece como firmante.
    """
    return (
        Usuario.objects.filter(
            rol__nombre_rol__in=[Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR],
            estado=Usuario.ACTIVO,
        )
        .exclude(firma="")
        .select_related("rol")
    )


def documentos_visibles(usuario):
    """
    Documentos que el usuario puede ver según su rol.

    El Contador Junior solo ve los documentos de los clientes que tiene
    asignados como responsable.
    """
    consulta = Documento.objects.select_related("cliente", "plantilla", "usuario_generador")
    if usuario.es_contador_junior:
        consulta = consulta.filter(cliente__responsable=usuario)
    return consulta


def filtrar_historico(usuario, plantilla=None, desde=None, hasta=None):
    """Aplica los filtros desplegables del histórico; todos son opcionales."""
    consulta = documentos_visibles(usuario)
    if plantilla:
        consulta = consulta.filter(plantilla=plantilla)
    if desde:
        consulta = consulta.filter(fecha_generacion__date__gte=desde)
    if hasta:
        consulta = consulta.filter(fecha_generacion__date__lte=hasta)
    return consulta


def documentos_del_cliente(usuario, cliente, limite=10):
    """Documentos generados para un cliente, para el panel de su ficha."""
    return documentos_visibles(usuario).filter(cliente=cliente)[:limite]


def _contexto_fijo(cliente, periodo, descripcion, fecha_expedicion=None):
    """Datos comunes a cualquier plantilla: cliente, período, despacho y fecha."""
    despacho = ConfiguracionDespacho.objects.first()
    return {
        "cliente": cliente.nombre_razon_social,
        "tipo_documento_cliente": cliente.get_tipo_documento_display(),
        "identificacion_cliente": cliente.nit_cedula,
        "periodo": periodo,
        "descripcion": descripcion,
        "nombre_despacho": despacho.nombre_despacho if despacho else "",
        "ciudad_despacho": despacho.ciudad if despacho else "",
        "fecha_expedicion": date_format(fecha_expedicion or timezone.localdate()),
    }


def contexto_render_documento(documento):
    """
    Arma el diccionario con el que se renderiza `texto_predeterminado`.

    Combina los datos fijos (cliente, período, despacho, fecha) con los
    valores propios de la plantilla capturados en `DocumentoValor` y, si la
    plantilla tiene campos repetibles, las filas agrupadas de
    `DocumentoDetalle` en `filas_repetibles`.
    """
    contexto = _contexto_fijo(
        documento.cliente,
        documento.periodo,
        documento.descripcion,
        fecha_expedicion=timezone.localtime(documento.fecha_generacion).date(),
    )

    for valor in documento.valores.select_related("campo"):
        contexto[clave_variable_campo(valor.campo.nombre_campo)] = valor.valor

    filas = {}
    for detalle in documento.detalles.select_related("campo"):
        fila = filas.setdefault(detalle.fila, {})
        fila[clave_variable_campo(detalle.campo.nombre_campo)] = detalle.valor
    contexto["filas_repetibles"] = [filas[numero] for numero in sorted(filas)]

    return contexto


def contexto_previsualizacion(*, cliente, periodo, descripcion, valores_simples, filas_repetibles):
    """
    Arma el mismo contexto que `contexto_render_documento`, pero a partir de
    los datos capturados en el formulario, antes de guardarlos como
    `Documento`/`DocumentoValor`/`DocumentoDetalle` — se usa en la
    previsualización del paso de confirmación.

    `valores_simples` es `{id_campo: valor}` y `filas_repetibles` es una
    lista de `{id_campo: valor}`, ya sin el prefijo `campo_` del formulario.
    """
    contexto = _contexto_fijo(cliente, periodo, descripcion)

    ids_campos = list(valores_simples) + [id_campo for fila in filas_repetibles for id_campo in fila]
    campos = CampoPlantilla.objects.in_bulk(ids_campos)

    for id_campo, valor in valores_simples.items():
        contexto[clave_variable_campo(campos[id_campo].nombre_campo)] = valor

    contexto["filas_repetibles"] = [
        {clave_variable_campo(campos[id_campo].nombre_campo): valor for id_campo, valor in fila.items()}
        for fila in filas_repetibles
    ]
    return contexto


def renderizar_texto(texto_predeterminado, contexto):
    """
    Renderiza un `texto_predeterminado` con un contexto ya armado.

    Es la única fuente de verdad para interpretar los marcadores de una
    plantilla: la reutilizan la previsualización, el detalle del documento y
    la construcción del PDF, para no repetir la lógica ni el escape de HTML
    en cada lugar. El autoescape de `django.template.Context` (activo por
    defecto) neutraliza cualquier `<`, `>` o `&` capturado en los valores
    antes de convertir los saltos de línea en `<br/>`.
    """
    plantilla = Template(texto_predeterminado)
    # mark_safe es seguro aquí: las variables ya fueron escapadas por el
    # autoescape de Context (activo por defecto) y el texto literal que las
    # rodea solo lo edita el Administrador (RolRequeridoMixin en las vistas
    # de gestión de plantillas), nunca un valor capturado de otro rol.
    return mark_safe(plantilla.render(Context(contexto)).replace("\n", "<br/>"))  # nosec


def texto_certificado_renderizado(documento):
    """Renderiza `texto_predeterminado` de la plantilla con los datos del documento."""
    return renderizar_texto(documento.plantilla.texto_predeterminado, contexto_render_documento(documento))
