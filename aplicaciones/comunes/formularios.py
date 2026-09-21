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
