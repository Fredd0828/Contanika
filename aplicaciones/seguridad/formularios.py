"""Formularios del módulo 8: equipo de trabajo, roles, permisos y perfil propio."""

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordChangeForm

from aplicaciones.comunes.formularios import FormularioBase, MixinEstilosBootstrap, ModeloFormularioBase

from .models import Rol, Usuario

TAMANO_MAXIMO_IMAGEN = 2 * 1024 * 1024


def _validar_imagen(archivo, descripcion):
    """El tipo lo valida `ImageField`; aquí se limita el tamaño."""
    if archivo and hasattr(archivo, "size") and archivo.size > TAMANO_MAXIMO_IMAGEN:
        raise forms.ValidationError(f"La imagen de {descripcion} no debe superar los 2 MB.")
    return archivo


def campo_confirmar_administrador():
    """Casilla para confirmar que habrá más de un Administrador activo (HU022-5)."""
    return forms.BooleanField(required=False, label="Confirmo que habrá más de un Administrador activo")


class UsuarioCrearForm(ModeloFormularioBase):
    """Alta de un miembro del equipo con su rol y una contraseña temporal (HU022-1)."""

    clave_temporal = forms.CharField(
        label="Contraseña temporal",
        widget=forms.PasswordInput(render_value=True, attrs={"autocomplete": "new-password"}),
        help_text="Se envía al correo del usuario; podrá cambiarla en «Mi perfil».",
    )
    confirmar_otro_administrador = campo_confirmar_administrador()

    class Meta:
        model = Usuario
        fields = ["nombre", "correo", "telefono", "rol"]
        labels = {"correo": "Correo electrónico", "telefono": "Teléfono"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rol"].empty_label = None

    def clean_correo(self):
        return self.cleaned_data["correo"].strip().lower()

    def clean(self):
        datos = super().clean()
        clave = datos.get("clave_temporal")
        if clave:
            usuario = Usuario(nombre=datos.get("nombre", ""), correo=datos.get("correo", ""))
            try:
                password_validation.validate_password(clave, usuario)
            except forms.ValidationError as error:
                self.add_error("clave_temporal", error)
        return datos


class UsuarioEditarForm(ModeloFormularioBase):
    """
    Datos que el Administrador edita de un usuario, incluidos el correo y el
    rol (que el usuario no puede cambiar en su perfil, HU024-3). La contraseña
    temporal es opcional: si se escribe, reemplaza la actual.
    """

    clave_temporal = forms.CharField(
        label="Nueva contraseña temporal",
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Déjela vacía para conservar la actual. Si la cambia, se envía al correo del usuario.",
    )
    confirmar_otro_administrador = campo_confirmar_administrador()

    class Meta:
        model = Usuario
        fields = ["nombre", "correo", "telefono", "rol", "identificacion", "numero_tarjeta_profesional"]
        labels = {
            "correo": "Correo electrónico",
            "telefono": "Teléfono",
            "identificacion": "Identificación",
            "numero_tarjeta_profesional": "Tarjeta profesional",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rol"].empty_label = None

    def clean_correo(self):
        return self.cleaned_data["correo"].strip().lower()

    def clean(self):
        datos = super().clean()
        clave = datos.get("clave_temporal")
        if clave:
            try:
                password_validation.validate_password(clave, self.instance)
            except forms.ValidationError as error:
                self.add_error("clave_temporal", error)
        return datos


class FiltroUsuariosForm(FormularioBase):
    """Filtros desplegables del listado del equipo."""

    texto = forms.CharField(required=False, label="Nombre o correo")
    rol = forms.ModelChoiceField(
        required=False, label="Rol", queryset=Rol.objects.all(), empty_label="Todos los roles"
    )
    estado = forms.ChoiceField(
        required=False, label="Estado", choices=[("", "Todos")] + Usuario.OPCIONES_ESTADO
    )


class PerfilForm(ModeloFormularioBase):
    """
    Perfil propio (HU024): nombre, teléfono, foto y, para quienes firman
    documentos, identificación, tarjeta profesional y firma. El correo y el
    rol solo los cambia el Administrador.
    """

    CAMPOS_FIRMA = ["identificacion", "numero_tarjeta_profesional", "firma"]

    class Meta:
        model = Usuario
        fields = ["nombre", "telefono", "foto", "identificacion", "numero_tarjeta_profesional", "firma"]
        labels = {
            "telefono": "Teléfono",
            "foto": "Foto de perfil",
            "identificacion": "Identificación",
            "numero_tarjeta_profesional": "Tarjeta profesional",
            "firma": "Imagen de la firma",
        }
        widgets = {
            "foto": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "firma": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    def __init__(self, *args, firmante=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not firmante:
            for campo in self.CAMPOS_FIRMA:
                del self.fields[campo]

    def clean_foto(self):
        return _validar_imagen(self.cleaned_data.get("foto"), "perfil")

    def clean_firma(self):
        return _validar_imagen(self.cleaned_data.get("firma"), "la firma")


class CambiarClaveForm(MixinEstilosBootstrap, PasswordChangeForm):
    """Cambio de contraseña propia: exige la contraseña actual (HU024-4)."""
