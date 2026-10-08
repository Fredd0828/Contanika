"""Formularios del módulo 5: hallazgos y revisiones contables."""

from django import forms
from django.contrib.auth import get_user_model

from aplicaciones.comunes.formularios import FormularioBase, ModeloFormularioBase, validar_archivo_adjunto

from . import selectores
from .models import Hallazgo

Usuario = get_user_model()


class HallazgoForm(ModeloFormularioBase):
    """
    Datos de registro y edición de un hallazgo.

    El estado y la observación de cierre no se editan aquí: cambian
    únicamente a través de `CambiarEstadoHallazgoForm`.
    """

    class Meta:
        model = Hallazgo
        fields = [
            "cliente",
            "tipo_hallazgo",
            "fecha_inicio_periodo",
            "fecha_fin_periodo",
            "responsable",
            "prioridad",
            "descripcion",
        ]
        widgets = {
            "fecha_inicio_periodo": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin_periodo": forms.DateInput(attrs={"type": "date"}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "tipo_hallazgo": forms.TextInput(attrs={"list": "lista-tipos-hallazgo"}),
        }
        labels = {"tipo_hallazgo": "Tipo de hallazgo"}

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cliente"].queryset = selectores.clientes_para_hallazgos(usuario)
        self.fields["responsable"].queryset = Usuario.objects.filter(estado=Usuario.ACTIVO)


class CambiarEstadoHallazgoForm(FormularioBase):
    """Cambia el estado del hallazgo; exige observación al cerrar."""

    estado = forms.ChoiceField(choices=Hallazgo.OPCIONES_ESTADO, label="Estado")
    observacion_cierre = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
        label="Observación de cierre",
    )

    def clean(self):
        datos = super().clean()
        if datos.get("estado") == Hallazgo.CERRADO and not datos.get("observacion_cierre"):
            raise forms.ValidationError("Debe registrar una observación de cierre para cerrar el hallazgo.")
        return datos


class AdjuntoHallazgoForm(FormularioBase):
    """Archivo de soporte a adjuntar a un hallazgo."""

    archivo = forms.FileField(label="Archivo")

    def clean_archivo(self):
        return validar_archivo_adjunto(self.cleaned_data["archivo"])


class FiltroHallazgosForm(FormularioBase):
    """Filtros desplegables del listado de hallazgos."""

    tipo = forms.CharField(required=False, label="Tipo de hallazgo")
    estado = forms.ChoiceField(required=False, label="Estado", choices=())
    responsable = forms.ModelChoiceField(required=False, label="Responsable", queryset=Usuario.objects.none())
    desde = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Desde")
    hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Hasta")

    def __init__(self, *args, usuario=None, opciones=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["estado"].choices = [("", "Todos los estados")] + list(Hallazgo.OPCIONES_ESTADO)
        self.fields["responsable"].queryset = Usuario.objects.filter(estado=Usuario.ACTIVO)
        self.fields["tipo"].widget.attrs["list"] = "lista-tipos-hallazgo"
