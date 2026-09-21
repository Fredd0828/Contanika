"""Registro de los modelos compartidos en el panel de administración."""

from django.contrib import admin

from .models import Adjunto


@admin.register(Adjunto)
class AdjuntoAdmin(admin.ModelAdmin):
    list_display = ["nombre_archivo", "tabla_origen", "id_origen", "fecha_carga"]
    list_filter = ["tabla_origen"]
    search_fields = ["nombre_archivo"]
