"""Registro de los modelos del módulo 1 en el panel de administración."""

from django.contrib import admin

from .models import (
    Cliente,
    ClienteMunicipio,
    ClienteObligacion,
    ClienteServicio,
    Credencial,
    ObligacionTributaria,
    TipoServicio,
)


class ClienteMunicipioInline(admin.TabularInline):
    model = ClienteMunicipio
    extra = 0


class ClienteServicioInline(admin.TabularInline):
    model = ClienteServicio
    extra = 0


class ClienteObligacionInline(admin.TabularInline):
    model = ClienteObligacion
    extra = 0


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        "nombre_razon_social",
        "nit_cedula",
        "tipo_documento",
        "tipo_persona",
        "regimen_tributario",
        "estado",
    ]
    list_filter = ["estado", "tipo_documento", "tipo_persona", "regimen_tributario", "ciudad"]
    search_fields = ["nombre_razon_social", "nit_cedula"]
    inlines = [ClienteMunicipioInline, ClienteServicioInline, ClienteObligacionInline]


@admin.register(TipoServicio)
class TipoServicioAdmin(admin.ModelAdmin):
    list_display = ["nombre_servicio"]
    search_fields = ["nombre_servicio"]


@admin.register(ObligacionTributaria)
class ObligacionTributariaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "ambito"]
    list_filter = ["ambito"]
    search_fields = ["nombre"]


@admin.register(Credencial)
class CredencialAdmin(admin.ModelAdmin):
    list_display = ["concepto", "cliente", "usuario_acceso", "fecha_ultima_actualizacion"]
    list_filter = ["concepto"]
    search_fields = ["concepto", "usuario_acceso", "cliente__nombre_razon_social"]
