"""Configuración de la aplicación del asistente de consultas."""

from django.apps import AppConfig


class AsistenteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.asistente"
    verbose_name = "Asistente de consultas"
