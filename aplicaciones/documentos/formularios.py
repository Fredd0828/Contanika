"""Formularios del módulo 4: expedición de documentos y certificados."""

import re

from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory

from aplicaciones.comunes.formularios import (
    FormularioBase,
    ModeloFormularioBase,
    validar_imagen_subida,
)
from aplicaciones.seguridad.models import ConfiguracionDespacho

from . import selectores
from .models import CampoPlantilla, Documento, Plantilla

Usuario = get_user_model()

TAMANO_MAXIMO_IMAGEN = 2 * 1024 * 1024


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


def _miles(entero):
    return f"{entero:,}".replace(",", ".")


class CampoPesos(forms.CharField):
    """
    Valor en pesos: solo números, con puntos de miles y hasta dos decimales
    con coma. Se guarda ya formateado («1.250.000» o «1.250.000,50») para
    que el documento lo imprima así, después del «$» de la plantilla.
    """

    patron = re.compile(r"^(\d{1,3}(\.\d{3})+|\d+)(,\d{1,2})?$")
    mensaje = "Escriba solo el valor en números, por ejemplo 1.250.000 (sin letras ni el signo $)."

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "widget", forms.TextInput(attrs={"inputmode": "decimal", "placeholder": "1.250.000"})
        )
        super().__init__(*args, **kwargs)
        self.widget.attrs["data-solo-numeros"] = "pesos"

    def clean(self, valor):
        valor = super().clean(valor)
        if not valor:
            return valor
        texto = valor.replace("$", "").replace(" ", "")
        if not self.patron.match(texto):
            raise forms.ValidationError(self.mensaje)
        entero, _, decimales = texto.replace(".", "").partition(",")
        resultado = _miles(int(entero))
        if decimales and int(decimales):
            resultado += "," + decimales.ljust(2, "0")
        return resultado


class CampoNumero(forms.CharField):
    """Número sin puntos ni letras (identificaciones): solo dígitos."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", forms.TextInput(attrs={"inputmode": "numeric"}))
        super().__init__(*args, **kwargs)
        self.widget.attrs["data-solo-numeros"] = "digitos"

    def clean(self, valor):
        valor = super().clean(valor)
        if valor and not valor.isdigit():
            raise forms.ValidationError("Escriba solo números, sin letras, puntos, guiones ni espacios.")
        return valor


class CampoPorcentaje(forms.CharField):
    """Porcentaje de 0 a 100, con hasta dos decimales con coma (33,33)."""

    patron = re.compile(r"^\d{1,3}([,.]\d{1,2})?$")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", forms.TextInput(attrs={"inputmode": "decimal", "placeholder": "50"}))
        super().__init__(*args, **kwargs)
        self.widget.attrs["data-solo-numeros"] = "decimal"

    def clean(self, valor):
        valor = super().clean(valor)
        if not valor:
            return valor
        texto = valor.replace("%", "").replace(" ", "")
        if not self.patron.match(texto) or float(texto.replace(",", ".")) > 100:
            raise forms.ValidationError(
                "Escriba un porcentaje entre 0 y 100, por ejemplo 33,5 (sin el signo %)."
            )
        return texto.replace(".", ",")


CAMPOS_POR_TIPO_DATO = {
    CampoPlantilla.PESOS: CampoPesos,
    CampoPlantilla.NUMERO: CampoNumero,
    CampoPlantilla.PORCENTAJE: CampoPorcentaje,
}


def campo_formulario(campo, **kwargs):
    """Campo de formulario que corresponde al tipo de dato de un `CampoPlantilla`."""
    clase = CAMPOS_POR_TIPO_DATO.get(campo.tipo_dato)
    if clase:
        return clase(label=campo.nombre_campo, **kwargs)
    return forms.CharField(label=campo.nombre_campo, **kwargs)


def construir_formulario_campos_simples(plantilla, datos=None):
    """
    Construye dinámicamente un formulario con un campo por cada `CampoPlantilla`
    Simple de la plantilla, nombrado `campo_<id_campo>`. Los de texto van en
    un área de texto; los de pesos, número o porcentaje solo aceptan números.
    """
    campos = {}
    for campo in selectores.campos_simples(plantilla):
        if campo.tipo_dato in CAMPOS_POR_TIPO_DATO:
            campos[f"campo_{campo.pk}"] = campo_formulario(campo)
        else:
            campos[f"campo_{campo.pk}"] = campo_formulario(campo, widget=forms.Textarea(attrs={"rows": 2}))
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
    campos = {f"campo_{campo.pk}": campo_formulario(campo, required=False) for campo in campos_repetibles}
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
        fields = ["nombre_campo", "tipo_campo", "tipo_dato"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si no se elige, se toma el que corresponde al nombre («Valor…» → pesos).
        self.fields["tipo_dato"].required = False

    def clean_tipo_dato(self):
        return self.cleaned_data.get("tipo_dato") or CampoPlantilla.tipo_dato_sugerido(
            self.cleaned_data.get("nombre_campo") or ""
        )

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
    fields=["nombre_campo", "tipo_campo", "tipo_dato"],
    extra=1,
    can_delete=True,
)


class MiFirmaForm(ModeloFormularioBase):
    """Firma, identificación y tarjeta profesional del contador que la carga."""

    class Meta:
        model = Usuario
        fields = ["firma", "identificacion", "numero_tarjeta_profesional"]
        widgets = {
            "firma": forms.ClearableFileInput(attrs={"accept": ".jpg,.jpeg,.png"}),
        }

    def clean_firma(self):
        """Solo JPG o PNG de hasta 2 MB (que sea una imagen real lo valida `ImageField`)."""
        return validar_imagen_subida(self.cleaned_data.get("firma"), "la firma", TAMANO_MAXIMO_IMAGEN)


class DatosDespachoForm(ModeloFormularioBase):
    """Datos fijos del despacho y membrete que encabeza los documentos en PDF."""

    class Meta:
        model = ConfiguracionDespacho
        fields = [
            "nombre_despacho",
            "nit_despacho",
            "membrete",
            "ciudad",
            "direccion",
            "telefono",
            "correo",
            "dias_aviso_vencimientos",
        ]
        widgets = {
            "membrete": forms.ClearableFileInput(attrs={"accept": ".jpg,.jpeg,.png"}),
        }
        labels = {"membrete": "Logo del despacho"}
        help_texts = {
            "nombre_despacho": (
                "Opcional. Si carga el logo y deja el nombre vacío, el encabezado de los PDF "
                "muestra solo el logo."
            ),
            "membrete": "JPG o PNG de hasta 2 MB. Al elegirlo puede recortarlo y ver sus medidas.",
        }

    def clean_nombre_despacho(self):
        return (self.cleaned_data.get("nombre_despacho") or "").strip()

    def clean(self):
        """El encabezado de los PDF necesita el nombre o el logo (o ambos)."""
        datos = super().clean()
        # Sin cambios, `membrete` trae el logo actual; si se marcó «Limpiar», llega False.
        sin_logo = not datos.get("membrete") and "membrete" not in self.errors
        if "nombre_despacho" in datos and not datos["nombre_despacho"] and sin_logo:
            self.add_error(
                "nombre_despacho",
                "Escriba el nombre del despacho o cargue su logo: los PDF necesitan uno de los dos.",
            )
        return datos

    def clean_membrete(self):
        """Solo JPG o PNG de hasta 2 MB (que sea una imagen real lo valida `ImageField`)."""
        return validar_imagen_subida(self.cleaned_data.get("membrete"), "el membrete", TAMANO_MAXIMO_IMAGEN)


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
