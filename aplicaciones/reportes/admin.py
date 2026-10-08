"""Registro de los modelos de reportes en el panel de administración."""

from django.contrib import admin

from .models import DescargaReporte, PermisoReporteRol, Reporte


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


@admin.register(DescargaReporte)
class DescargaReporteAdmin(admin.ModelAdmin):
    """Registro de auditoría: solo consulta."""

    list_display = ["fecha_hora", "reporte", "formato", "usuario"]
    list_filter = ["reporte", "formato"]
    list_select_related = ["reporte", "usuario"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
