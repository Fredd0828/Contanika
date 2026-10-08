"""Formularios del módulo 3: tablero de tareas Kanban."""

from django import forms
from django.contrib.auth import get_user_model

from aplicaciones.comunes.formularios import FormularioBase, ModeloFormularioBase

from .models import ObservacionTarea, Tarea

Usuario = get_user_model()


class TareaForm(ModeloFormularioBase):
    """
    Alta y edición de una tarjeta del tablero Kanban.

    El estado no se edita aquí: cambia únicamente desde el tablero (arrastre
    o el selector de la tarjeta), para conservar el historial de cambios.
    """

    tipo_tarea = forms.CharField(
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={"list": "lista-tipos-tarea"}),
        label="Tipo de tarea",
    )

    class Meta:
        model = Tarea
        fields = [
            "cliente",
            "titulo",
            "descripcion",
            "tipo_tarea",
            "responsable",
            "prioridad",
            "fecha_vencimiento",
            "mostrar_en_calendario",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
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
        """Exige fecha de vencimiento cuando la tarea se marca para el calendario."""
        datos = super().clean()
        if datos.get("mostrar_en_calendario") and not datos.get("fecha_vencimiento"):
            self.add_error(
                "fecha_vencimiento",
                "Indique la fecha de vencimiento para mostrarla en el calendario.",
            )
        return datos


class CambiarEstadoTareaForm(FormularioBase):
    """Cambio rápido del estado de una tarea (arrastre o selector)."""

    estado = forms.ChoiceField(choices=Tarea.OPCIONES_ESTADO, label="Estado")


class ObservacionTareaForm(ModeloFormularioBase):
    """Observación de avance registrada sobre una tarea."""

    class Meta:
        model = ObservacionTarea
        fields = ["contenido"]
        widgets = {
            "contenido": forms.Textarea(attrs={"rows": 2, "placeholder": "Registrar avance…"}),
        }


class FiltroTareasForm(FormularioBase):
    """Filtros desplegables del tablero de tareas."""

    cliente = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="Cliente",
        empty_label="Todos los clientes",
    )
    responsable = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(estado=Usuario.ACTIVO),
        required=False,
        label="Responsable",
        empty_label="Todos los responsables",
    )
    prioridad = forms.ChoiceField(
        choices=[("", "Todas las prioridades")] + list(Tarea.OPCIONES_PRIORIDAD),
        required=False,
        label="Prioridad",
    )
    tipo_tarea = forms.ChoiceField(choices=(), required=False, label="Tipo de tarea")

    def __init__(self, *args, usuario=None, opciones=None, **kwargs):
        super().__init__(*args, **kwargs)
        opciones = opciones or {}
        self.fields["tipo_tarea"].choices = [("", "Todos los tipos")] + [
            (tipo, tipo) for tipo in opciones.get("tipos_tarea", [])
        ]

        from aplicaciones.clientes.models import Cliente

        clientes = Cliente.objects.filter(estado=Cliente.ACTIVO)
        if usuario is not None and usuario.es_contador_junior:
            clientes = clientes.filter(responsable=usuario)
        self.fields["cliente"].queryset = clientes
