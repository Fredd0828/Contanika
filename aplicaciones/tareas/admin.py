"""Registro de los modelos del módulo 3 en el panel de administración."""

from django.contrib import admin

from .models import HistorialTarea, ObservacionTarea, Tarea


class HistorialTareaInline(admin.TabularInline):
    model = HistorialTarea
    extra = 0
    readonly_fields = ["usuario", "estado_anterior", "estado_nuevo", "fecha_cambio"]


class ObservacionTareaInline(admin.TabularInline):
    model = ObservacionTarea
    extra = 0


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ["titulo", "cliente", "responsable", "prioridad", "estado", "fecha_vencimiento"]
    list_filter = ["estado", "prioridad", "mostrar_en_calendario"]
    search_fields = ["titulo", "cliente__nombre_razon_social"]
    inlines = [HistorialTareaInline, ObservacionTareaInline]
