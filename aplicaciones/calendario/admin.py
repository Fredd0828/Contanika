"""Registro de los modelos del módulo 2 en el panel de administración."""

from django.contrib import admin

from .models import (
    AnotacionCalendario,
    AnotacionCalendarioDestinatario,
    ConfiguracionAlerta,
    TablaReferenciaDian,
    Vencimiento,
)


class ConfiguracionAlertaInline(admin.TabularInline):
    model = ConfiguracionAlerta
    extra = 0


@admin.register(TablaReferenciaDian)
class TablaReferenciaDianAdmin(admin.ModelAdmin):
    list_display = ["tipo_obligacion", "grupo_nit", "fecha_vencimiento", "periodo_gravable"]
    list_filter = ["tipo_obligacion", "periodo_gravable"]
    search_fields = ["tipo_obligacion", "grupo_nit"]


@admin.register(Vencimiento)
class VencimientoAdmin(admin.ModelAdmin):
    list_display = [
        "cliente",
        "tipo_obligacion",
        "ambito",
        "fecha_vencimiento",
        "estado_presentacion",
        "estado_validacion",
    ]
    list_filter = ["ambito", "estado_presentacion", "estado_validacion"]
    search_fields = ["cliente__nombre_razon_social", "tipo_obligacion"]
    inlines = [ConfiguracionAlertaInline]


@admin.register(AnotacionCalendario)
class AnotacionCalendarioAdmin(admin.ModelAdmin):
    list_display = ["fecha", "autor", "visibilidad"]
    list_filter = ["visibilidad", "fecha"]
    search_fields = ["contenido"]


@admin.register(AnotacionCalendarioDestinatario)
class AnotacionCalendarioDestinatarioAdmin(admin.ModelAdmin):
    list_display = ["anotacion_calendario", "usuario"]
