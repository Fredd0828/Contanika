"""Registro de los modelos del módulo 5 en el panel de administración."""

from django.contrib import admin

from .models import Hallazgo


@admin.register(Hallazgo)
class HallazgoAdmin(admin.ModelAdmin):
    list_display = ["tipo_hallazgo", "cliente", "prioridad", "estado", "fecha_inicio_periodo"]
    list_filter = ["estado", "prioridad", "tipo_hallazgo"]
    search_fields = ["cliente__nombre_razon_social", "descripcion"]
