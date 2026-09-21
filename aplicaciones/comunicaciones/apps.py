"""Configuración de la aplicación del módulo 7: comunicaciones integradas."""

from django.apps import AppConfig


class ComunicacionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.comunicaciones"
    verbose_name = "Comunicaciones integradas"
