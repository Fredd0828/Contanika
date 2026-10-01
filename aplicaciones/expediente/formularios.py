"""Formularios del módulo 9: expediente y bitácora por cliente."""

from django import forms

from aplicaciones.comunes.formularios import (
    CampoVariosArchivos,
    FormularioBase,
    ModeloFormularioBase,
    validar_archivo_adjunto,
)

from . import selectores
from .models import Anotacion

# Máximo de adjuntos por anotación: 5 para Administrador y Senior (HU025-1),
# 3 para el Contador Junior (HU027-2).
MAXIMO_ADJUNTOS = 5
MAXIMO_ADJUNTOS_JUNIOR = 3


def maximo_adjuntos(usuario):
    return MAXIMO_ADJUNTOS_JUNIOR if usuario.es_contador_junior else MAXIMO_ADJUNTOS


class AnotacionForm(ModeloFormularioBase):
    """
    Registro de una anotación en el expediente del cliente.

    El usuario y la fecha y hora de registro los fija el sistema; aquí solo se
    capturan el cliente, el tipo, la fecha del evento, el contenido y los
    archivos de soporte.
    """

    archivos = CampoVariosArchivos(required=False, label="Archivos de soporte")

    class Meta:
        model = Anotacion
        fields = ["cliente", "tipo_anotacion", "fecha", "contenido"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "contenido": forms.Textarea(attrs={"rows": 5}),
            "tipo_anotacion": forms.TextInput(attrs={"list": "lista-tipos-anotacion"}),
        }
        labels = {
            "tipo_anotacion": "Tipo de anotación",
            "fecha": "Fecha",
            "contenido": "Contenido",
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.maximo_adjuntos = maximo_adjuntos(usuario)
        self.fields["cliente"].queryset = selectores.clientes_visibles(usuario).order_by(
            "nombre_razon_social"
        )
        ayuda = f"Hasta {self.maximo_adjuntos} archivos (PDF, Word, Excel o imagen, máximo 10 MB cada uno)."
        self.fields["archivos"].help_text = ayuda

    def clean_tipo_anotacion(self):
        return self.cleaned_data["tipo_anotacion"].strip()

    def clean_archivos(self):
        archivos = self.cleaned_data.get("archivos") or []
        if len(archivos) > self.maximo_adjuntos:
            raise forms.ValidationError(
                f"Puede adjuntar máximo {self.maximo_adjuntos} archivos por anotación."
            )
        errores = []
        for archivo in archivos:
            try:
                validar_archivo_adjunto(archivo)
            except forms.ValidationError as error:
                errores.extend(error.messages)
        if errores:
            raise forms.ValidationError(errores)
        return archivos


class FiltroAnotacionesForm(FormularioBase):
    """Filtros desplegables del expediente: cliente, tipo y rango de fechas."""

    cliente = forms.ModelChoiceField(
        required=False, label="Cliente", queryset=None, empty_label="Todos los clientes"
    )
    tipo = forms.CharField(required=False, label="Tipo de anotación")
    desde = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Desde")
    hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Hasta")
    incluir_archivadas = forms.BooleanField(required=False, label="Incluir archivadas")

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cliente"].queryset = selectores.clientes_visibles(usuario).order_by(
            "nombre_razon_social"
        )
        self.fields["tipo"].widget.attrs["list"] = "lista-tipos-anotacion"
