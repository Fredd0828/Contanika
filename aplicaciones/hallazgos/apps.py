"""Configuración de la aplicación del módulo 5: hallazgos y revisiones."""

from django.apps import AppConfig


class HallazgosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.hallazgos"
    verbose_name = "Hallazgos y revisiones"
