"""Registro de los modelos del módulo 4 en el panel de administración."""

from django.contrib import admin

from .models import CampoPlantilla, Documento, DocumentoDetalle, DocumentoValor, Plantilla


class CampoPlantillaInline(admin.TabularInline):
    model = CampoPlantilla
    extra = 0


@admin.register(Plantilla)
class PlantillaAdmin(admin.ModelAdmin):
    list_display = ["nombre_plantilla", "tipo_documento"]
    search_fields = ["nombre_plantilla", "tipo_documento"]
    inlines = [CampoPlantillaInline]


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ["plantilla", "cliente", "usuario_generador", "fecha_generacion"]
    list_filter = ["plantilla"]
    search_fields = ["cliente__nombre_razon_social", "descripcion"]


@admin.register(DocumentoValor)
class DocumentoValorAdmin(admin.ModelAdmin):
    list_display = ["documento", "campo", "valor"]


@admin.register(DocumentoDetalle)
class DocumentoDetalleAdmin(admin.ModelAdmin):
    list_display = ["documento", "campo", "fila", "valor"]
