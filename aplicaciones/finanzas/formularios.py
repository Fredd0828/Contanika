"""Formularios del módulo 6: honorarios, catálogos y cuentas de cobro."""

from decimal import Decimal

from django import forms
from django.forms import BaseFormSet, formset_factory
from django.utils import timezone

from aplicaciones.comunes.formularios import FormularioBase, ModeloFormularioBase

from . import selectores, servicios
from .models import (
    OPCIONES_CANAL_ENVIO,
    ConceptoFacturable,
    ConfiguracionCobro,
    CuentaBancaria,
    CuentaCobro,
    EnvioProgramado,
    Honorario,
    MetodoPago,
)
from .templatetags.finanzas_tags import formato_pesos

CAMPO_MONTO = {"max_digits": 12, "decimal_places": 2, "min_value": Decimal("0")}


# ---------------------------------------------------------------------------
# Honorario del cliente (HU044)
# ---------------------------------------------------------------------------


class HonorarioForm(FormularioBase):
    """
    Tipo y monto del honorario del cliente. Además del monto fijo, agrega un
    campo de monto por cada tipo de servicio del cliente (`servicio_<id>`),
    que se usa cuando el honorario es "Por servicio".
    """

    tipo = forms.ChoiceField(choices=Honorario.OPCIONES_TIPO, label="Tipo de honorario")
    monto = forms.DecimalField(required=False, label="Monto fijo mensual", **CAMPO_MONTO)

    def __init__(self, *args, cliente, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipos_servicio = selectores.tipos_servicio_del_cliente(cliente)
        for tipo_servicio in self.tipos_servicio:
            self.fields[f"servicio_{tipo_servicio.pk}"] = forms.DecimalField(
                required=False,
                label=tipo_servicio.nombre_servicio,
                widget=forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
                **CAMPO_MONTO,
            )

    def campos_servicio(self):
        """Campos de monto por servicio, en el orden de los servicios del cliente."""
        return [self[f"servicio_{tipo_servicio.pk}"] for tipo_servicio in self.tipos_servicio]

    def montos_por_servicio(self):
        """`{tipo_servicio: monto}` con los montos capturados por servicio."""
        return {
            tipo_servicio: self.cleaned_data.get(f"servicio_{tipo_servicio.pk}")
            for tipo_servicio in self.tipos_servicio
        }

    def clean(self):
        datos = super().clean()
        if datos.get("tipo") == Honorario.POR_SERVICIO:
            if not self.tipos_servicio:
                raise forms.ValidationError(
                    "El cliente no tiene tipos de servicio asociados; agréguelos en su ficha "
                    "o configure un honorario fijo mensual."
                )
            if not any(monto for monto in self.montos_por_servicio().values()):
                raise forms.ValidationError("Indique el monto de al menos un servicio.")
        elif not datos.get("monto"):
            self.add_error("monto", "Indique el monto fijo mensual del honorario.")
        return datos


# ---------------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------------


class ConceptoFacturableForm(ModeloFormularioBase):
    class Meta:
        model = ConceptoFacturable
        fields = ["nombre_concepto", "valor_sugerido"]
        labels = {"nombre_concepto": "Concepto", "valor_sugerido": "Valor sugerido"}


class CuentaBancariaForm(ModeloFormularioBase):
    class Meta:
        model = CuentaBancaria
        fields = ["banco", "tipo_cuenta", "numero_cuenta", "titular"]
        labels = {"tipo_cuenta": "Tipo de cuenta", "numero_cuenta": "Número de cuenta"}
        widgets = {"tipo_cuenta": forms.TextInput(attrs={"list": "lista-tipos-cuenta"})}


class MetodoPagoForm(ModeloFormularioBase):
    class Meta:
        model = MetodoPago
        fields = ["nombre_metodo"]
        labels = {"nombre_metodo": "Método de pago"}


# ---------------------------------------------------------------------------
# Cuenta de cobro (HU016, HU049)
# ---------------------------------------------------------------------------


class CuentaCobroForm(ModeloFormularioBase):
    """Datos generales de la cuenta de cobro (las líneas van en `LineasCobroFormSet`)."""

    class Meta:
        model = CuentaCobro
        fields = [
            "cliente",
            "periodo_facturado",
            "fecha_inicio_periodo",
            "fecha_fin_periodo",
            "valor_total",
            "fecha_vencimiento_pago",
            "cuenta_bancaria",
            "metodo_pago",
        ]
        labels = {
            "periodo_facturado": "Período facturado",
            "fecha_inicio_periodo": "Inicio del período",
            "fecha_fin_periodo": "Fin del período",
            "valor_total": "Valor total a cobrar",
            "fecha_vencimiento_pago": "Fecha de vencimiento del pago",
            "cuenta_bancaria": "Cuenta bancaria para el pago",
            "metodo_pago": "Método de pago",
        }
        help_texts = {
            "fecha_fin_periodo": "Solo para el período personalizado; en los demás se calcula solo.",
        }
        widgets = {
            "fecha_inicio_periodo": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "fecha_fin_periodo": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "fecha_vencimiento_pago": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cliente"].queryset = selectores.clientes_para_cobro(usuario)
        self.fields["fecha_inicio_periodo"].required = True
        self.fields["cuenta_bancaria"].empty_label = "Sin cuenta bancaria"
        self.fields["metodo_pago"].empty_label = "Sin método específico"

    def clean_valor_total(self):
        valor = self.cleaned_data.get("valor_total")
        if valor is not None and valor <= 0:
            raise forms.ValidationError("El valor total debe ser mayor que cero.")
        return valor

    def clean(self):
        datos = super().clean()
        periodo = datos.get("periodo_facturado")
        inicio = datos.get("fecha_inicio_periodo")
        fin = datos.get("fecha_fin_periodo")
        if periodo == CuentaCobro.PERSONALIZADO:
            if not fin:
                self.add_error("fecha_fin_periodo", "Indique la fecha final del período personalizado.")
            elif inicio and fin < inicio:
                self.add_error("fecha_fin_periodo", "La fecha final no puede ser anterior a la inicial.")
        elif inicio:
            datos["fecha_fin_periodo"] = servicios.calcular_fin_periodo(periodo, inicio)
        return datos


class LineaCobroForm(FormularioBase):
    """
    Una línea de la descripción del servicio. Todos los campos son opcionales
    a nivel de fila: las filas vacías (por ejemplo, las que el usuario quitó)
    se ignoran, y el formset valida el conjunto.
    """

    concepto = forms.ModelChoiceField(
        queryset=ConceptoFacturable.objects.all(),
        required=False,
        empty_label="Texto libre",
    )
    descripcion_linea = forms.CharField(max_length=200, required=False)
    valor_linea = forms.DecimalField(required=False, **CAMPO_MONTO)


class BaseLineasCobroFormSet(BaseFormSet):
    """
    Valida las líneas de servicio: al menos una, y si alguna lleva valor
    individual, la suma de los valores debe ser igual al valor total (HU049).
    La vista asigna `valor_total` antes de validar.
    """

    valor_total = None

    def lineas(self):
        """Líneas capturadas con descripción, en el orden del formulario."""
        resultado = []
        for formulario in self.forms:
            datos = getattr(formulario, "cleaned_data", {}) or {}
            concepto = datos.get("concepto")
            descripcion = (datos.get("descripcion_linea") or "").strip()
            if not descripcion and concepto:
                descripcion = concepto.nombre_concepto
            if descripcion:
                resultado.append(
                    {
                        "concepto": concepto,
                        "descripcion_linea": descripcion,
                        "valor_linea": datos.get("valor_linea"),
                    }
                )
        return resultado

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        for formulario in self.forms:
            datos = formulario.cleaned_data
            sin_descripcion = not (datos.get("descripcion_linea") or "").strip() and not datos.get("concepto")
            if sin_descripcion and datos.get("valor_linea"):
                raise forms.ValidationError("Cada línea con valor debe tener una descripción o un concepto.")
        lineas = self.lineas()
        if not lineas:
            raise forms.ValidationError("Agregue al menos una línea en la descripción del servicio.")
        valores = [linea["valor_linea"] for linea in lineas if linea["valor_linea"]]
        if valores and self.valor_total is not None:
            suma = sum(valores, Decimal("0"))
            if suma != self.valor_total:
                raise forms.ValidationError(
                    f"La suma de los valores por línea ({formato_pesos(suma)}) debe ser igual al "
                    f"valor total ({formato_pesos(self.valor_total)})."
                )


LineasCobroFormSet = formset_factory(LineaCobroForm, formset=BaseLineasCobroFormSet, extra=0)


class FiltroCuentasCobroForm(FormularioBase):
    """Filtros desplegables del histórico de cuentas de cobro."""

    cliente = forms.ModelChoiceField(queryset=None, required=False, empty_label="Todos los clientes")
    estado_pago = forms.ChoiceField(
        choices=[("", "Todos los estados")] + CuentaCobro.OPCIONES_ESTADO_PAGO,
        required=False,
        label="Estado de pago",
    )
    periodo = forms.ChoiceField(
        choices=[("", "Todos los períodos")] + CuentaCobro.OPCIONES_PERIODO,
        required=False,
        label="Período",
    )
    desde = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Desde")
    hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Hasta")

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cliente"].queryset = selectores.clientes_para_cobro(usuario)


# ---------------------------------------------------------------------------
# Envíos (HU045-HU047 y programación)
# ---------------------------------------------------------------------------

ENVIAR_AHORA = "ahora"
PROGRAMAR = "programar"


class EnvioForm(FormularioBase):
    """Qué enviar, por qué canal y cuándo: ahora mismo o en una fecha y hora."""

    tipo = forms.ChoiceField(choices=EnvioProgramado.OPCIONES_TIPO, label="Qué enviar")
    canal = forms.ChoiceField(choices=OPCIONES_CANAL_ENVIO, label="Canal")
    modo = forms.ChoiceField(
        choices=[(ENVIAR_AHORA, "Enviar ahora"), (PROGRAMAR, "Programar para una fecha y hora")],
        initial=ENVIAR_AHORA,
        label="Cuándo",
    )
    fecha_programada = forms.DateTimeField(
        required=False,
        label="Fecha y hora del envío",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
    )

    def clean(self):
        datos = super().clean()
        if datos.get("modo") == PROGRAMAR:
            fecha = datos.get("fecha_programada")
            if not fecha:
                self.add_error("fecha_programada", "Indique la fecha y hora del envío programado.")
            elif fecha <= timezone.now():
                self.add_error("fecha_programada", "La fecha del envío programado debe ser futura.")
        return datos


class EnvioMasivoForm(EnvioForm):
    """Envío masivo: además del tipo, canal y momento, las cuentas seleccionadas (HU046, HU047)."""

    cuentas = forms.ModelMultipleChoiceField(
        queryset=CuentaCobro.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        error_messages={"required": "Seleccione al menos una cuenta de cobro."},
    )

    def __init__(self, *args, candidatas, **kwargs):
        super().__init__(*args, **kwargs)
        self.candidatas = candidatas
        # Solo se aceptan cuentas de la lista de candidatas visibles para el usuario.
        self.fields["cuentas"].queryset = CuentaCobro.objects.filter(pk__in=[c.pk for c in candidatas])


class ConfiguracionCobroForm(ModeloFormularioBase):
    """Parámetros del cobro mensual automático y de los recordatorios automáticos."""

    class Meta:
        model = ConfiguracionCobro
        fields = [
            "cobro_automatico_activo",
            "dia_generacion",
            "dias_plazo_pago",
            "canal_cobro",
            "cuenta_bancaria",
            "metodo_pago",
            "recordatorios_activos",
            "dias_antes_vencimiento",
            "frecuencia_mora_dias",
            "canal_recordatorio",
        ]
        labels = {
            "cobro_automatico_activo": "Generar y enviar el cobro mensual automáticamente",
            "dia_generacion": "Día del mes en que se genera",
            "dias_plazo_pago": "Días de plazo para pagar",
            "canal_cobro": "Canal de envío de la cuenta",
            "cuenta_bancaria": "Cuenta bancaria para el pago",
            "metodo_pago": "Método de pago",
            "recordatorios_activos": "Enviar recordatorios de pago automáticamente",
            "dias_antes_vencimiento": "Recordar cuántos días antes del vencimiento",
            "frecuencia_mora_dias": "Repetir en mora cada (días)",
            "canal_recordatorio": "Canal del recordatorio",
        }

    def clean_dia_generacion(self):
        dia = self.cleaned_data["dia_generacion"]
        if not 1 <= dia <= 28:
            raise forms.ValidationError("Elija un día entre 1 y 28, para que exista en todos los meses.")
        return dia

    def clean_frecuencia_mora_dias(self):
        dias = self.cleaned_data["frecuencia_mora_dias"]
        if dias < 1:
            raise forms.ValidationError("La frecuencia debe ser de al menos un día.")
        return dias
