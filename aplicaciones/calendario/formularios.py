"""Formularios del módulo 2: tabla DIAN, vencimientos, alertas y anotaciones."""

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from aplicaciones.comunes.formularios import FormularioBase, ModeloFormularioBase

from .models import (
    AnotacionCalendario,
    ConfiguracionAlerta,
    TablaReferenciaDian,
    Vencimiento,
)

Usuario = get_user_model()


class TablaReferenciaDianForm(ModeloFormularioBase):
    """Carga manual de una fila de la tabla de referencia DIAN (Administrador)."""

    tipo_obligacion = forms.CharField(
        max_length=40,
        widget=forms.TextInput(attrs={"list": "lista-obligaciones"}),
        label="Tipo de obligación",
    )

    class Meta:
        model = TablaReferenciaDian
        fields = ["tipo_obligacion", "grupo_nit", "fecha_vencimiento", "periodo_gravable"]
        widgets = {
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def clean(self):
        """Evita duplicados de obligación + grupo + período al cargar a mano."""
        datos = super().clean()
        consulta = TablaReferenciaDian.objects.filter(
            tipo_obligacion=datos.get("tipo_obligacion"),
            grupo_nit=datos.get("grupo_nit"),
            periodo_gravable=datos.get("periodo_gravable"),
        )
        if self.instance.pk:
            consulta = consulta.exclude(pk=self.instance.pk)
        if consulta.exists():
            raise forms.ValidationError(
                "Ya existe una referencia con esa obligación, grupo de NIT y período."
            )
        return datos


class ImportarDianForm(FormularioBase):
    """Carga masiva de la tabla de referencia DIAN desde un archivo Excel."""

    archivo = forms.FileField(
        label="Archivo de Excel (.xlsx)",
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx"}),
    )

    def clean_archivo(self):
        """Valida la extensión y el tamaño antes de procesar el archivo."""
        archivo = self.cleaned_data["archivo"]
        if not archivo.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("El archivo debe estar en formato Excel (.xlsx).")
        if archivo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("El archivo no debe superar los 5 MB.")
        return archivo


class VencimientoManualForm(ModeloFormularioBase):
    """
    Registro manual de vencimientos distritales, municipales o casos especiales.

    El tipo de obligación es una selección abierta; el municipio aplica solo
    cuando el ámbito es distrital o municipal.
    """

    tipo_obligacion = forms.CharField(
        max_length=40,
        widget=forms.TextInput(attrs={"list": "lista-obligaciones"}),
        label="Tipo de obligación",
    )

    class Meta:
        model = Vencimiento
        fields = [
            "cliente",
            "tipo_obligacion",
            "ambito",
            "municipio",
            "fecha_vencimiento",
            "responsable",
            "estado_presentacion",
        ]
        widgets = {
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "municipio": forms.TextInput(attrs={"list": "lista-municipios"}),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsable"].queryset = Usuario.objects.filter(estado=Usuario.ACTIVO)
        self.fields["responsable"].required = False

        clientes = self.fields["cliente"].queryset.filter(estado="Activo")
        if usuario is not None and usuario.es_contador_junior:
            clientes = clientes.filter(responsable=usuario)
        self.fields["cliente"].queryset = clientes

    def clean(self):
        """Exige municipio cuando el ámbito es distrital o municipal."""
        datos = super().clean()
        ambito = datos.get("ambito")
        municipio = (datos.get("municipio") or "").strip()
        if ambito in (Vencimiento.DISTRITAL, Vencimiento.MUNICIPAL) and not municipio:
            self.add_error("municipio", "Indique el municipio o distrito del vencimiento.")
        return datos


class ConfiguracionAlertaForm(ModeloFormularioBase):
    """Configuración de una alerta automática para un vencimiento."""

    class Meta:
        model = ConfiguracionAlerta
        fields = ["dias_anticipacion", "canal"]

    def clean_dias_anticipacion(self):
        """La anticipación debe estar entre 0 y 60 días."""
        dias = self.cleaned_data["dias_anticipacion"]
        if dias > 60:
            raise forms.ValidationError("La anticipación no puede superar los 60 días.")
        return dias


class AnotacionCalendarioForm(ModeloFormularioBase):
    """Anotación libre del calendario con visibilidad configurable."""

    destinatarios = forms.ModelMultipleChoiceField(
        queryset=Usuario.objects.filter(estado=Usuario.ACTIVO),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Compañeros etiquetados",
        help_text="Solo aplica cuando la visibilidad es “Por etiqueta”.",
    )

    class Meta:
        model = AnotacionCalendario
        fields = ["fecha", "contenido", "visibilidad"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "contenido": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        """Exige al menos un destinatario cuando la visibilidad es por etiqueta."""
        datos = super().clean()
        if datos.get("visibilidad") == AnotacionCalendario.POR_ETIQUETA and not datos.get("destinatarios"):
            self.add_error(
                "destinatarios",
                "Etiquete al menos un compañero o elija otra visibilidad.",
            )
        return datos


class FiltroCalendarioForm(FormularioBase):
    """Filtros desplegables del calendario y del listado de vencimientos."""

    cliente = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="Cliente",
        empty_label="Todos los clientes",
    )
    ambito = forms.ChoiceField(
        choices=[("", "Todos los ámbitos")] + list(Vencimiento.OPCIONES_AMBITO),
        required=False,
        label="Ámbito",
    )
    estado_presentacion = forms.ChoiceField(
        choices=[("", "Todos los estados")] + list(Vencimiento.OPCIONES_ESTADO_PRESENTACION),
        required=False,
        label="Estado de presentación",
    )
    tipo_obligacion = forms.ChoiceField(
        choices=(),
        required=False,
        label="Tipo de obligación",
    )
    responsable = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(estado=Usuario.ACTIVO),
        required=False,
        label="Responsable",
        empty_label="Todos los responsables",
    )

    def __init__(self, *args, usuario=None, opciones=None, **kwargs):
        super().__init__(*args, **kwargs)
        opciones = opciones or {}

        tipos = [("", "Todos los tipos")] + [(tipo, tipo) for tipo in opciones.get("tipos_obligacion", [])]
        self.fields["tipo_obligacion"].choices = tipos

        from aplicaciones.clientes.models import Cliente

        clientes = Cliente.objects.filter(estado=Cliente.ACTIVO)
        if usuario is not None and usuario.es_contador_junior:
            clientes = clientes.filter(responsable=usuario)
        self.fields["cliente"].queryset = clientes


class CambiarEstadoForm(FormularioBase):
    """Cambio rápido del estado de presentación de un vencimiento."""

    estado_presentacion = forms.ChoiceField(
        choices=Vencimiento.OPCIONES_ESTADO_PRESENTACION,
        label="Estado de presentación",
    )


class FiltroFechaMixin:
    """Utilidad para leer fechas de los parámetros GET de las vistas."""

    @staticmethod
    def parse_fecha(valor):
        """Convierte 'AAAA-MM-DD' a date; devuelve None si es inválido."""
        try:
            return timezone.datetime.strptime(valor, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None
