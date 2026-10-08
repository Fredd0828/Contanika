"""Registro de los modelos del módulo 7 en el panel de administración."""

from django.contrib import admin

from .models import Comunicacion


@admin.register(Comunicacion)
class ComunicacionAdmin(admin.ModelAdmin):
    """El historial no se edita ni se elimina (HU020-4, HU021-3): solo consulta."""

    list_display = ["cliente", "canal", "tipo", "estado_envio", "fecha_hora", "modulo_origen"]
    list_filter = ["canal", "tipo", "estado_envio"]
    search_fields = ["cliente__nombre_razon_social", "contenido_resumen"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
