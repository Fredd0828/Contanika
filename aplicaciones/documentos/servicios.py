"""
Reglas de negocio del módulo 4: gestión de plantillas y generación de documentos.

Las vistas no escriben directamente en varios modelos ni arman el PDF: llaman
a estas funciones, que agrupan cada operación en una transacción para que la
plantilla (con sus campos) o el documento (con sus valores, detalles y
archivo) queden consistentes.
"""

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import ProtectedError
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.html import escape
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, Spacer

from aplicaciones.comunes import paleta
from aplicaciones.comunes.pdf import (
    ancho_util,
    color,
    construir_pdf,
    encabezado_documento,
    estilos_documento,
    imagen_proporcional,
)
from aplicaciones.seguridad.models import ConfiguracionDespacho

from . import selectores
from .models import Documento, DocumentoDetalle, DocumentoValor

# Espacio reservado para la firma del contador en el PDF.
ANCHO_FIRMA = 5 * cm
ALTO_FIRMA = 2.5 * cm
# Un certificado se lee como carta: márgenes laterales más amplios.
MARGEN_DOCUMENTO = 2.6 * cm


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
    ancho = ancho_util(letter, MARGEN_DOCUMENTO)
    textos = estilos_documento()
    despacho = ConfiguracionDespacho.objects.first()
    fecha = date_format(timezone.localtime(documento.fecha_generacion).date())

    elementos = encabezado_documento(
        despacho,
        ancho,
        f"Documento No. {documento.pk}",
        [f"Expedido el {fecha}"],
        textos,
    )
    elementos.append(Spacer(1, 0.9 * cm))
    elementos.append(
        Paragraph(escape(documento.plantilla.nombre_plantilla).upper(), textos["titulo_centrado"])
    )
    # Una línea corta bajo el título lo separa del cuerpo, como en un certificado impreso.
    elementos.append(
        HRFlowable(
            width=2.6 * cm,
            thickness=1.4,
            color=color(paleta.TEAL),
            spaceBefore=7,
            spaceAfter=22,
            hAlign="CENTER",
        )
    )
    elementos.append(Paragraph(selectores.texto_certificado_renderizado(documento), textos["cuerpo"]))
    elementos.append(Spacer(1, 1.6 * cm))
    elementos.append(bloque_firma(usuario_firmante, None))

    return construir_pdf(
        elementos,
        tamano=letter,
        titulo=documento.plantilla.nombre_plantilla,
        despacho=despacho,
        margen_lateral=MARGEN_DOCUMENTO,
    )


class _NombreConLinea(Paragraph):
    """Nombre del firmante con la línea de firma dibujada encima."""

    def draw(self):
        lienzo = self.canv
        lienzo.saveState()
        lienzo.setStrokeColor(color(paleta.NAVY))
        lienzo.setLineWidth(0.7)
        lienzo.line(0, self.height + 3, ANCHO_FIRMA + 1.5 * cm, self.height + 3)
        lienzo.restoreState()
        super().draw()


def bloque_firma(usuario_firmante, estilos):
    """
    Firma y datos del contador que firma el documento.

    Todo el bloque va al costado izquierdo, en la misma línea del cuerpo del
    documento: la imagen de la firma (sin deformarla), la línea de firma y
    debajo el nombre, la identificación y la tarjeta profesional. Se mantiene
    junto para que un salto de página no separe la firma de los datos.

    `estilos` se conserva por compatibilidad; el bloque usa los estilos
    comunes de los PDF.
    """
    textos = estilos_documento()
    if usuario_firmante.firma:
        firma = imagen_proporcional(usuario_firmante.firma.path, ANCHO_FIRMA, ALTO_FIRMA, alineacion="LEFT")
    else:
        firma = Spacer(1, ALTO_FIRMA)
    nombre = ParagraphStyle("firmante", parent=textos["valor"], spaceBefore=6)
    elementos = [firma, _NombreConLinea(escape(usuario_firmante.nombre), nombre)]
    if usuario_firmante.identificacion:
        elementos.append(Paragraph(f"C.C. {escape(usuario_firmante.identificacion)}", textos["normal"]))
    if usuario_firmante.numero_tarjeta_profesional:
        elementos.append(
            Paragraph(f"T.P. No. {escape(usuario_firmante.numero_tarjeta_profesional)}", textos["normal"])
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
