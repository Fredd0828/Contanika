"""
Reglas de negocio del módulo 4: gestión de plantillas y generación de documentos.

Las vistas no escriben directamente en varios modelos ni arman el PDF: llaman
a estas funciones, que agrupan cada operación en una transacción para que la
plantilla (con sus campos) o el documento (con sus valores, detalles y
archivo) queden consistentes.
"""

import io

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import ProtectedError
from django.utils.html import escape
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer

from aplicaciones.comunes.pdf import encabezado_despacho, imagen_proporcional
from aplicaciones.seguridad.models import ConfiguracionDespacho

from . import selectores
from .models import Documento, DocumentoDetalle, DocumentoValor

# Espacio reservado para la firma del contador en el PDF.
ANCHO_FIRMA = 5 * cm
ALTO_FIRMA = 2.5 * cm


@transaction.atomic
def crear_plantilla(formulario, formset_campos):
    """Crea una plantilla nueva junto con sus campos propios."""
    plantilla = formulario.save()
    formset_campos.instance = plantilla
    formset_campos.save()
    return plantilla


@transaction.atomic
def actualizar_plantilla(plantilla, formulario, formset_campos):
    """
    Actualiza el texto predeterminado y los campos de una plantilla.

    Un campo con documentos ya generados no se puede eliminar (protegido por
    la relación con `DocumentoValor`/`DocumentoDetalle`); si el formset
    intenta borrarlo, se convierte el error de integridad en un error de
    negocio legible para que la vista lo muestre en el formulario en vez de
    devolver un error de servidor.
    """
    try:
        plantilla = formulario.save()
        formset_campos.instance = plantilla
        formset_campos.save()
    except ProtectedError as error:
        raise ValueError("No se puede eliminar un campo que ya tiene documentos generados.") from error
    return plantilla


@transaction.atomic
def generar_documento(
    *,
    cliente,
    plantilla,
    periodo,
    descripcion,
    usuario_firmante,
    usuario_generador,
    valores_simples,
    filas_repetibles,
):
    """
    Genera un documento: crea el registro, sus valores/detalles y el PDF.

    `valores_simples` es un diccionario `{id_campo: valor}` para los campos
    simples de la plantilla. `filas_repetibles` es una lista de diccionarios
    `{id_campo: valor}`, una por fila (por ejemplo, un accionista), que se
    numeran desde 1 al guardarse como `DocumentoDetalle`.
    """
    documento = Documento.objects.create(
        cliente=cliente,
        plantilla=plantilla,
        periodo=periodo,
        descripcion=descripcion,
        usuario_generador=usuario_generador,
    )
    DocumentoValor.objects.bulk_create(
        DocumentoValor(documento=documento, campo_id=id_campo, valor=valor)
        for id_campo, valor in valores_simples.items()
    )
    DocumentoDetalle.objects.bulk_create(
        DocumentoDetalle(documento=documento, campo_id=id_campo, fila=numero_fila, valor=valor)
        for numero_fila, fila in enumerate(filas_repetibles, start=1)
        for id_campo, valor in fila.items()
    )
    pdf_bytes = construir_pdf_documento(documento, usuario_firmante)
    documento.archivo.save(f"documento_{documento.pk}.pdf", ContentFile(pdf_bytes), save=True)
    return documento


def construir_pdf_documento(documento, usuario_firmante):
    """
    Arma el PDF del documento generado con ReportLab (Platypus).

    El cuerpo se toma de `selectores.texto_certificado_renderizado`, que ya
    aplica el autoescape de Django sobre los valores capturados antes de
    convertir los saltos de línea en `<br/>`, para que ningún valor ingresado
    por un usuario pueda inyectar marcado interpretado por ReportLab.
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

    elementos = encabezado_despacho(despacho, estilos, ancho_maximo=documento_pdf.width)
    elementos.append(Spacer(1, 1 * cm))
    elementos.append(Paragraph(documento.plantilla.nombre_plantilla, estilos["Heading2"]))
    elementos.append(Spacer(1, 0.5 * cm))
    elementos.append(Paragraph(selectores.texto_certificado_renderizado(documento), estilos["Normal"]))
    elementos.append(Spacer(1, 2 * cm))
    elementos.append(bloque_firma(usuario_firmante, estilos))

    documento_pdf.build(elementos)
    return buffer.getvalue()


def bloque_firma(usuario_firmante, estilos):
    """
    Firma y datos del contador que firma el documento.

    Todo el bloque va al costado izquierdo, en la misma línea del cuerpo del
    documento: la imagen de la firma (sin deformarla) y debajo el nombre, la
    identificación y la tarjeta profesional. Se mantiene junto para que un
    salto de página no separe la firma de los datos.
    """
    if usuario_firmante.firma:
        firma = imagen_proporcional(usuario_firmante.firma.path, ANCHO_FIRMA, ALTO_FIRMA, alineacion="LEFT")
    else:
        firma = Spacer(1, ALTO_FIRMA)
    elementos = [firma, Paragraph(escape(usuario_firmante.nombre), estilos["Normal"])]
    if usuario_firmante.identificacion:
        elementos.append(Paragraph(f"C.C. {escape(usuario_firmante.identificacion)}", estilos["Normal"]))
    if usuario_firmante.numero_tarjeta_profesional:
        elementos.append(
            Paragraph(f"T.P. No. {escape(usuario_firmante.numero_tarjeta_profesional)}", estilos["Normal"])
        )
    return KeepTogether(elementos)


@transaction.atomic
def eliminar_documento(documento):
    """Elimina un documento generado junto con su archivo físico."""
    documento.archivo.delete(save=False)
    documento.delete()


def actualizar_firma(usuario, formulario):
    """Guarda la firma, identificación y tarjeta profesional del usuario."""
    return formulario.save()


def actualizar_datos_despacho(formulario):
    """Guarda los datos fijos del despacho (incluido el membrete) que se imprimen en los PDF."""
    return formulario.save()
