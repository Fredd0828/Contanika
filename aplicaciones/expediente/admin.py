"""Registro de los modelos del módulo 9 en el panel de administración."""

from django.contrib import admin

from .models import Anotacion


@admin.register(Anotacion)
class AnotacionAdmin(admin.ModelAdmin):
    """La bitácora es inmutable: desde el admin solo se cambia el estado de archivado."""

    list_display = ["tipo_anotacion", "cliente", "fecha", "usuario", "fecha_hora", "archivado"]
    list_filter = ["tipo_anotacion", "archivado"]
    search_fields = ["cliente__nombre_razon_social", "contenido"]
    readonly_fields = ["cliente", "tipo_anotacion", "fecha", "fecha_hora", "usuario", "contenido"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
