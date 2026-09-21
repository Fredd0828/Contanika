"""Registro de los modelos de reportes en el panel de administración."""

from django.contrib import admin

from .models import PermisoReporteRol, Reporte


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ["nombre_reporte", "modulo_origen"]
    search_fields = ["nombre_reporte", "modulo_origen"]


@admin.register(PermisoReporteRol)
class PermisoReporteRolAdmin(admin.ModelAdmin):
    list_display = ["rol", "reporte", "habilitado"]
    list_editable = ["habilitado"]
    list_filter = ["rol", "habilitado"]
    list_select_related = ["rol", "reporte"]
