"""Registro de los modelos de seguridad en el panel de administración."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as UserAdminBase
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import ConfiguracionDespacho, Modulo, PermisoRolModulo, Rol, Usuario


class UsuarioCreacionForm(UserCreationForm):
    """Formulario de creación de usuarios con los campos propios del sistema."""

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("correo", "nombre", "rol")


class UsuarioCambioForm(UserChangeForm):
    """Formulario de edición de usuarios con los campos propios del sistema."""

    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = "__all__"


@admin.register(Usuario)
class UsuarioAdmin(UserAdminBase):
    form = UsuarioCambioForm
    add_form = UsuarioCreacionForm
    model = Usuario
    ordering = ["nombre"]
    # El proyecto usa la tabla rol en lugar de los grupos de Django.
    filter_horizontal = ()
    list_display = ["correo", "nombre", "rol", "estado", "is_staff"]
    list_filter = ["rol", "estado", "is_staff"]
    search_fields = ["correo", "nombre", "numero_tarjeta_profesional", "identificacion"]
    fieldsets = (
        (None, {"fields": ("correo", "password")}),
        (
            "Datos personales",
            {
                "fields": (
                    "nombre",
                    "telefono",
                    "foto_url",
                    "identificacion",
                    "numero_tarjeta_profesional",
                    "firma",
                )
            },
        ),
        ("Rol y estado", {"fields": ("rol", "estado", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("correo", "nombre", "rol", "password1", "password2"),
            },
        ),
    )


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ["id_rol", "nombre_rol"]
    search_fields = ["nombre_rol"]


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ["codigo_modulo", "nombre_modulo"]
    search_fields = ["codigo_modulo", "nombre_modulo"]


@admin.register(PermisoRolModulo)
class PermisoRolModuloAdmin(admin.ModelAdmin):
    list_display = ["rol", "modulo", "habilitado"]
    list_editable = ["habilitado"]
    list_filter = ["rol", "habilitado"]
    list_select_related = ["rol", "modulo"]


@admin.register(ConfiguracionDespacho)
class ConfiguracionDespachoAdmin(admin.ModelAdmin):
    list_display = ["nombre_despacho", "nit_despacho", "ciudad"]
