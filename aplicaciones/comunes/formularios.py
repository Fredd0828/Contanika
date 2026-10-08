"""
Utilidades de formularios compartidas por los módulos del sistema.

Estas clases base agregan automáticamente las clases de Bootstrap 5 a los
campos, para que las plantillas no tengan que repetir esa configuración.
"""

from django import forms


class MixinEstilosBootstrap:
    """Asigna las clases de Bootstrap 5 a cada campo del formulario."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class FormularioBase(MixinEstilosBootstrap, forms.Form):
    """Formulario normal con estilos de Bootstrap."""


class ModeloFormularioBase(MixinEstilosBootstrap, forms.ModelForm):
    """Formulario de modelo con estilos de Bootstrap."""


# Archivos de soporte (tabla `adjunto`): hallazgos y anotaciones del expediente.
EXTENSIONES_PERMITIDAS = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png")
TAMANO_MAXIMO_ADJUNTO = 10 * 1024 * 1024


def validar_archivo_adjunto(archivo):
    """Rechaza formatos no permitidos y archivos de más de 10 MB."""
    if not archivo.name.lower().endswith(EXTENSIONES_PERMITIDAS):
        raise forms.ValidationError(
            f"«{archivo.name}»: formato no permitido. Use PDF, Word, Excel o una imagen (JPG/PNG)."
        )
    if archivo.size > TAMANO_MAXIMO_ADJUNTO:
        raise forms.ValidationError(f"«{archivo.name}»: el archivo no debe superar los 10 MB.")
    return archivo


class EntradaVariosArchivos(forms.ClearableFileInput):
    """Selector de archivos que permite elegir varios a la vez."""

    allow_multiple_selected = True


class CampoVariosArchivos(forms.FileField):
    """
    Campo que recibe una lista de archivos (patrón de la documentación de
    Django para subir varios archivos con un solo input).
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", EntradaVariosArchivos())
        super().__init__(*args, **kwargs)

    def clean(self, datos, inicial=None):
        if isinstance(datos, (list, tuple)):
            return [super(CampoVariosArchivos, self).clean(dato, inicial) for dato in datos]
        if not datos:
            return []
        return [super().clean(datos, inicial)]
