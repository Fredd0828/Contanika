"""Formularios del módulo 1: ficha del cliente y municipios adicionales."""

from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory

from aplicaciones.comunes.formularios import ModeloFormularioBase

from .models import Cliente, ClienteMunicipio, TipoServicio

Usuario = get_user_model()


class ClienteForm(ModeloFormularioBase):
    """
    Formulario de la ficha del cliente.

    Los campos de régimen tributario, ciudad y municipio funcionan como
    selección abierta (listas sugeridas con `datalist` que además permiten
    escribir un valor nuevo), conforme a las reglas transversales del sistema.
    """

    tipos_servicio = forms.ModelMultipleChoiceField(
        queryset=TipoServicio.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Tipos de servicio contable",
    )
    nuevo_tipo_servicio = forms.CharField(
        required=False,
        max_length=80,
        label="Otro tipo de servicio (escríbalo si no aparece en la lista)",
    )
    regimen_tributario = forms.CharField(
        required=False,
        max_length=40,
        widget=forms.TextInput(attrs={"list": "lista-regimenes"}),
        label="Régimen tributario",
    )
    ciudad = forms.CharField(
        required=False,
        max_length=60,
        widget=forms.TextInput(attrs={"list": "lista-ciudades"}),
        label="Ciudad",
    )
    municipio_principal = forms.CharField(
        required=False,
        max_length=60,
        widget=forms.TextInput(attrs={"list": "lista-municipios"}),
        label="Municipio principal",
    )

    class Meta:
        model = Cliente
        fields = [
            "nombre_razon_social",
            "nit_cedula",
            "tipo_persona",
            "regimen_tributario",
            "responsable_iva",
            "ciudad",
            "municipio_principal",
            "informacion_contacto",
            "responsable",
            "estado",
        ]
        widgets = {
            "informacion_contacto": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsable"].queryset = Usuario.objects.filter(estado=Usuario.ACTIVO)
        self.fields["responsable"].required = False
        if self.instance.pk:
            self.fields["tipos_servicio"].initial = self.instance.servicios.values_list(
                "tipo_servicio", flat=True
            )

    def clean_nit_cedula(self):
        """Evita registrar dos clientes con el mismo NIT o cédula."""
        nit = self.cleaned_data["nit_cedula"].strip()
        existentes = Cliente.objects.filter(nit_cedula__iexact=nit)
        if self.instance.pk:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise forms.ValidationError("Ya existe un cliente registrado con ese NIT o cédula.")
        return nit

    def servicios_seleccionados(self):
        """Tipos de servicio marcados más el que se haya escrito como nuevo."""
        seleccionados = list(self.cleaned_data.get("tipos_servicio", []))
        nuevo = (self.cleaned_data.get("nuevo_tipo_servicio") or "").strip()
        if nuevo:
            tipo, _ = TipoServicio.objects.get_or_create(nombre_servicio=nuevo)
            seleccionados.append(tipo)
        return seleccionados


class ClienteMunicipioForm(ModeloFormularioBase):
    """Municipio adicional donde el cliente tributa (multi-ICA)."""

    class Meta:
        model = ClienteMunicipio
        fields = ["municipio"]
        widgets = {
            "municipio": forms.TextInput(attrs={"list": "lista-municipios"}),
        }


ClienteMunicipioFormSet = inlineformset_factory(
    Cliente,
    ClienteMunicipio,
    form=ClienteMunicipioForm,
    fields=["municipio"],
    extra=1,
    can_delete=True,
)
