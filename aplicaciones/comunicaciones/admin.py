"""Registro de los modelos del módulo 7 en el panel de administración."""

from django.contrib import admin

from .models import Comunicacion


@admin.register(Comunicacion)
class ComunicacionAdmin(admin.ModelAdmin):
    list_display = ["cliente", "canal", "tipo", "estado_envio", "fecha_hora", "modulo_origen"]
    list_filter = ["canal", "tipo", "estado_envio"]
    search_fields = ["cliente__nombre_razon_social", "contenido_resumen"]
    readonly_fields = ["fecha_hora"]
