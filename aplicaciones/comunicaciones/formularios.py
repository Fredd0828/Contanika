"""Formularios del módulo 7: comunicaciones integradas."""

from datetime import timedelta

from django import forms
from django.utils import timezone

from aplicaciones.comunes.formularios import FormularioBase, ModeloFormularioBase

from . import selectores
from .models import Comunicacion


class ComunicacionManualForm(ModeloFormularioBase):
    """Registro manual de una comunicación hecha por un canal no automatizado (HU019)."""

    class Meta:
        model = Comunicacion
        fields = ["cliente", "canal", "fecha_hora", "contenido_resumen"]
        widgets = {
            "canal": forms.TextInput(attrs={"list": "lista-canales"}),
            "fecha_hora": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "contenido_resumen": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "canal": "Canal",
            "fecha_hora": "Fecha y hora",
            "contenido_resumen": "Resumen del contenido",
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cliente"].queryset = selectores.clientes_visibles(usuario).order_by(
            "nombre_razon_social"
        )
        self.fields["contenido_resumen"].required = True
        if not self.is_bound and "fecha_hora" not in self.initial:
            self.initial["fecha_hora"] = timezone.localtime().replace(second=0, microsecond=0)

    def clean_canal(self):
        return self.cleaned_data["canal"].strip()

    def clean_fecha_hora(self):
        """Lo registrado ya ocurrió: no se acepta una fecha y hora futura."""
        fecha_hora = self.cleaned_data["fecha_hora"]
        if fecha_hora > timezone.now() + timedelta(minutes=5):
            raise forms.ValidationError("La comunicación no puede tener una fecha y hora futura.")
        return fecha_hora


class FiltroComunicacionesForm(FormularioBase):
    """Filtros desplegables del historial: cliente, canal, tipo y rango de fechas."""

    cliente = forms.ModelChoiceField(
        required=False, label="Cliente", queryset=None, empty_label="Todos los clientes"
    )
    canal = forms.ChoiceField(required=False, label="Canal")
    tipo = forms.ChoiceField(
        required=False,
        label="Tipo",
        choices=[("", "Todos los tipos")] + Comunicacion.OPCIONES_TIPO,
    )
    desde = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Desde")
    hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Hasta")

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cliente"].queryset = selectores.clientes_visibles(usuario).order_by(
            "nombre_razon_social"
        )
        self.fields["canal"].choices = [("", "Todos los canales")] + [
            (canal, canal) for canal in selectores.canales(usuario)
        ]
