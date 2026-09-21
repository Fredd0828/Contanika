"""Configuración de la aplicación del módulo 10: reportes y análisis."""

from django.apps import AppConfig


class ReportesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.reportes"
    verbose_name = "Reportes y análisis"
