"""Registro de los modelos del módulo 9 en el panel de administración."""

from django.contrib import admin

from .models import Anotacion


@admin.register(Anotacion)
class AnotacionAdmin(admin.ModelAdmin):
    list_display = ["tipo_anotacion", "cliente", "usuario", "fecha_hora", "archivado"]
    list_filter = ["tipo_anotacion", "archivado"]
    search_fields = ["cliente__nombre_razon_social", "contenido"]
    readonly_fields = ["fecha_hora"]
