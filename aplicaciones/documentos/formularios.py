"""Formularios del módulo 4: expedición de documentos y certificados."""

from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory

from aplicaciones.comunes.formularios import FormularioBase, ModeloFormularioBase
from aplicaciones.seguridad.models import ConfiguracionDespacho

from . import selectores
from .models import CampoPlantilla, Documento, Plantilla

Usuario = get_user_model()


class GenerarDocumentoForm(ModeloFormularioBase):
    """Datos comunes a cualquier documento: cliente, plantilla, período, descripción y firma."""

    usuario_firmante = forms.ModelChoiceField(
        queryset=selectores.firmantes_disponibles(),
        label="Firma a usar",
        help_text="Solo aparecen los usuarios que ya tienen una firma cargada.",
    )

    class Meta:
        model = Documento
        fields = ["cliente", "plantilla", "periodo", "descripcion"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {"periodo": "Fecha o período"}

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cliente"].queryset = selectores.clientes_para_generar(usuario)
        self.fields["plantilla"].queryset = selectores.plantillas_activas()
        self.fields["usuario_firmante"].queryset = selectores.firmantes_disponibles()
        self.fields["periodo"].required = True


def construir_formulario_campos_simples(plantilla, datos=None):
    """
    Construye dinámicamente un formulario con un campo por cada `CampoPlantilla`
    Simple de la plantilla, nombrado `campo_<id_campo>`.
    """
    campos = {
        f"campo_{campo.pk}": forms.CharField(
            label=campo.nombre_campo,
            widget=forms.Textarea(attrs={"rows": 2}),
        )
        for campo in selectores.campos_simples(plantilla)
    }
    clase_formulario = type("CamposSimplesForm", (FormularioBase,), campos)
    return clase_formulario(datos)


def construir_formset_filas_repetibles(plantilla, datos=None, prefix="filas"):
    """
    Construye un formset con un campo por cada `CampoPlantilla` Repetible de la
    plantilla (por ejemplo, nombre y porcentaje de cada accionista). Devuelve
    `None` si la plantilla no tiene campos repetibles.
    """
    campos_repetibles = list(selectores.campos_repetibles(plantilla))
    if not campos_repetibles:
        return None
    campos = {
        f"campo_{campo.pk}": forms.CharField(label=campo.nombre_campo, required=False)
        for campo in campos_repetibles
    }
    clase_fila = type("FilaRepetibleForm", (FormularioBase,), campos)
    clase_formset = forms.formset_factory(clase_fila, extra=1, can_delete=True)
    return clase_formset(datos, prefix=prefix)


def valores_desde_cleaned_data(cleaned_data):
    """
    Convierte `{"campo_<id_campo>": valor}` (nombres de los campos dinámicos)
    en `{id_campo: valor}`, ignorando cualquier otra llave (por ejemplo,
    `DELETE` en una fila del formset de filas repetibles).
    """
    return {
        int(clave.removeprefix("campo_")): valor
        for clave, valor in cleaned_data.items()
        if clave.startswith("campo_")
    }


class PlantillaForm(ModeloFormularioBase):
    """Nombre, tipo y texto predeterminado de una plantilla de documento."""

    class Meta:
        model = Plantilla
        fields = ["nombre_plantilla", "tipo_documento", "texto_predeterminado"]
        widgets = {
            "texto_predeterminado": forms.Textarea(attrs={"rows": 10}),
        }
        help_texts = {
            "texto_predeterminado": (
                "Use marcadores como {{ cliente }} o {{ periodo }} para los datos "
                "automáticos, y el nombre de cada campo propio en minúsculas y "
                "guiones bajos, por ejemplo {{ concepto }}."
            ),
        }


class CampoPlantillaForm(ModeloFormularioBase):
    """Campo propio (simple o repetible) de una plantilla."""

    class Meta:
        model = CampoPlantilla
        fields = ["nombre_campo", "tipo_campo"]

    def save(self, commit=True):
        campo = super().save(commit=False)
        campo.es_repetible = campo.tipo_campo == CampoPlantilla.REPETIBLE
        if commit:
            campo.save()
        return campo


CampoPlantillaFormSet = inlineformset_factory(
    Plantilla,
    CampoPlantilla,
    form=CampoPlantillaForm,
    fields=["nombre_campo", "tipo_campo"],
    extra=1,
    can_delete=True,
)


class MiFirmaForm(ModeloFormularioBase):
    """Firma, identificación y tarjeta profesional del contador que la carga."""

    class Meta:
        model = Usuario
        fields = ["firma", "identificacion", "numero_tarjeta_profesional"]
        widgets = {
            "firma": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    def clean_firma(self):
        """Valida el tamaño de la imagen antes de guardarla (el tipo lo valida `ImageField`)."""
        archivo = self.cleaned_data.get("firma")
        if archivo and hasattr(archivo, "size") and archivo.size > 2 * 1024 * 1024:
            raise forms.ValidationError("La imagen de la firma no debe superar los 2 MB.")
        return archivo


class DatosDespachoForm(ModeloFormularioBase):
    """Datos fijos del despacho y membrete que encabeza los documentos en PDF."""

    class Meta:
        model = ConfiguracionDespacho
        fields = ["nombre_despacho", "nit_despacho", "membrete", "ciudad", "direccion", "telefono", "correo"]
        widgets = {
            "membrete": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    def clean_membrete(self):
        """Valida el tamaño de la imagen antes de guardarla (el tipo lo valida `ImageField`)."""
        archivo = self.cleaned_data.get("membrete")
        if archivo and hasattr(archivo, "size") and archivo.size > 2 * 1024 * 1024:
            raise forms.ValidationError("La imagen del membrete no debe superar los 2 MB.")
        return archivo


class FiltroHistoricoForm(FormularioBase):
    """Filtros desplegables del histórico de documentos generados."""

    plantilla = forms.ModelChoiceField(
        queryset=Plantilla.objects.all(),
        required=False,
        label="Tipo de documento",
        empty_label="Todos los tipos",
    )
    desde = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Desde")
    hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Hasta")
