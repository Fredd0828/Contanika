"""
Formularios de filtros del módulo 10: reportes y análisis.

Todos los reportes comparten los filtros generales del spec (período,
estado y responsable) más los propios de cada uno. Los campos de cliente
muestran solo los clientes que el usuario puede consultar.
"""

from django import forms
from django.contrib.auth import get_user_model

from aplicaciones.calendario.models import Vencimiento
from aplicaciones.clientes.models import Cliente, TipoServicio
from aplicaciones.comunes.formularios import FormularioBase
from aplicaciones.finanzas.models import CuentaCobro
from aplicaciones.tareas.models import Tarea

Usuario = get_user_model()


def _campo_fecha(etiqueta):
    return forms.DateField(required=False, label=etiqueta, widget=forms.DateInput(attrs={"type": "date"}))


def _opciones(valores, vacio):
    return [("", vacio)] + [(valor, valor) for valor in valores]


def clientes_visibles(usuario, todo_el_equipo=False):
    """
    Clientes que el usuario puede incluir en un reporte. En los reportes de
    todo el equipo (clientes, vencimientos y tareas) son todos; en los
    financieros, Senior y Junior solo los que tienen asignados.
    """
    consulta = Cliente.objects.order_by("nombre_razon_social")
    if not todo_el_equipo and not usuario.es_administrador:
        consulta = consulta.filter(responsable=usuario)
    return consulta


class FiltroBase(FormularioBase):
    """Período (desde/hasta) y responsable, comunes a los reportes."""

    # True en los reportes que todo el equipo ve completos (clientes, vencimientos y tareas).
    todo_el_equipo = False

    desde = _campo_fecha("Desde")
    hasta = _campo_fecha("Hasta")
    responsable = forms.ModelChoiceField(
        required=False, label="Responsable", queryset=Usuario.objects.none(), empty_label="Todos"
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        if "responsable" in self.fields:
            self.fields["responsable"].queryset = Usuario.objects.filter(estado=Usuario.ACTIVO)
        if "cliente" in self.fields:
            self.fields["cliente"].queryset = clientes_visibles(usuario, self.todo_el_equipo)

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("desde"), datos.get("hasta")
        if desde and hasta and desde > hasta:
            raise forms.ValidationError("La fecha «Desde» no puede ser posterior a «Hasta».")
        return datos

    def resumen_filtros(self):
        """Filtros aplicados en texto legible, para el encabezado y el registro de descargas."""
        if not self.is_valid():
            return ""
        partes = []
        for nombre, valor in self.cleaned_data.items():
            if valor in (None, "", False):
                continue
            etiqueta = self.fields[nombre].label
            if hasattr(valor, "strftime"):
                valor = valor.strftime("%d/%m/%Y")
            elif valor is True:
                valor = "Sí"
            partes.append(f"{etiqueta}: {valor}")
        return " · ".join(partes)


class FiltroClientesForm(FiltroBase):
    """Reporte de clientes: régimen, ciudad, estado, servicio y responsable; período = fecha de registro."""

    todo_el_equipo = True

    regimen = forms.ChoiceField(required=False, label="Régimen")
    ciudad = forms.ChoiceField(required=False, label="Ciudad")
    estado = forms.ChoiceField(
        required=False, label="Estado", choices=_opciones(["Activo", "Inactivo"], "Todos")
    )
    servicio = forms.ModelChoiceField(
        required=False, label="Tipo de servicio", queryset=TipoServicio.objects.all(), empty_label="Todos"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        visibles = clientes_visibles(self.usuario, self.todo_el_equipo)
        regimenes = visibles.exclude(regimen_tributario="").values_list("regimen_tributario", flat=True)
        ciudades = visibles.exclude(ciudad="").values_list("ciudad", flat=True)
        self.fields["regimen"].choices = _opciones(sorted(set(regimenes)), "Todos")
        self.fields["ciudad"].choices = _opciones(sorted(set(ciudades)), "Todas")
        self.fields["desde"].label = "Registrado desde"
        self.fields["hasta"].label = "Registrado hasta"


class FiltroVencimientosForm(FiltroBase):
    """Reporte de vencimientos (HU029): período, cliente, tipo, ámbito, estado y responsable."""

    todo_el_equipo = True

    cliente = forms.ModelChoiceField(
        required=False, label="Cliente", queryset=Cliente.objects.none(), empty_label="Todos"
    )
    tipo_obligacion = forms.ChoiceField(required=False, label="Tipo de obligación")
    ambito = forms.ChoiceField(
        required=False, label="Ámbito", choices=[("", "Todos")] + Vencimiento.OPCIONES_AMBITO
    )
    estado = forms.ChoiceField(
        required=False,
        label="Estado de presentación",
        choices=[("", "Todos")] + Vencimiento.OPCIONES_ESTADO_PRESENTACION,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tipos = Vencimiento.objects.values_list("tipo_obligacion", flat=True).distinct()
        self.fields["tipo_obligacion"].choices = _opciones(sorted(set(tipos)), "Todos")


class FiltroCarteraForm(FiltroBase):
    """Reporte de cartera: cliente y responsable; el período filtra el historial de abonos."""

    cliente = forms.ModelChoiceField(
        required=False, label="Cliente", queryset=Cliente.objects.none(), empty_label="Todos"
    )
    incluir_al_dia = forms.BooleanField(required=False, label="Incluir clientes al día")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["desde"].label = "Abonos desde"
        self.fields["hasta"].label = "Abonos hasta"


class FiltroCuentasCobroForm(FiltroBase):
    """Reporte de cuentas de cobro: período de generación, cliente, estados y responsable."""

    cliente = forms.ModelChoiceField(
        required=False, label="Cliente", queryset=Cliente.objects.none(), empty_label="Todos"
    )
    estado_pago = forms.ChoiceField(
        required=False, label="Estado de pago", choices=[("", "Todos")] + CuentaCobro.OPCIONES_ESTADO_PAGO
    )
    estado_envio = forms.ChoiceField(
        required=False, label="Estado de envío", choices=[("", "Todos")] + CuentaCobro.OPCIONES_ESTADO_ENVIO
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["desde"].label = "Generadas desde"
        self.fields["hasta"].label = "Generadas hasta"


class FiltroTareasForm(FiltroBase):
    """Reporte de tareas (HU051): cliente, responsable, estado, prioridad y rango de vencimiento."""

    todo_el_equipo = True

    cliente = forms.ModelChoiceField(
        required=False, label="Cliente", queryset=Cliente.objects.none(), empty_label="Todos"
    )
    estado = forms.ChoiceField(
        required=False, label="Estado", choices=[("", "Todos")] + Tarea.OPCIONES_ESTADO
    )
    prioridad = forms.ChoiceField(
        required=False, label="Prioridad", choices=[("", "Todas")] + Tarea.OPCIONES_PRIORIDAD
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["desde"].label = "Vencen desde"
        self.fields["hasta"].label = "Vencen hasta"


class FiltroIngresosForm(FiltroBase):
    """Reporte de ingresos (HU048): rango de meses; solo total consolidado del despacho."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields["responsable"]
        self.fields["desde"].help_text = "Por defecto, los últimos 12 meses."
