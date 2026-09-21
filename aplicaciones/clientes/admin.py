"""Registro de los modelos del módulo 1 en el panel de administración."""

from django.contrib import admin

from .models import Cliente, ClienteMunicipio, ClienteServicio, Credencial, TipoServicio


class ClienteMunicipioInline(admin.TabularInline):
    model = ClienteMunicipio
    extra = 0


class ClienteServicioInline(admin.TabularInline):
    model = ClienteServicio
    extra = 0


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["nombre_razon_social", "nit_cedula", "tipo_persona", "regimen_tributario", "estado"]
    list_filter = ["estado", "tipo_persona", "regimen_tributario", "ciudad"]
    search_fields = ["nombre_razon_social", "nit_cedula"]
    inlines = [ClienteMunicipioInline, ClienteServicioInline]


@admin.register(TipoServicio)
class TipoServicioAdmin(admin.ModelAdmin):
    list_display = ["nombre_servicio"]
    search_fields = ["nombre_servicio"]


@admin.register(Credencial)
class CredencialAdmin(admin.ModelAdmin):
    list_display = ["concepto", "cliente", "usuario_acceso", "fecha_ultima_actualizacion"]
    list_filter = ["concepto"]
    search_fields = ["concepto", "usuario_acceso", "cliente__nombre_razon_social"]
