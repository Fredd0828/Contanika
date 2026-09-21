"""Configuración de la aplicación del módulo 2: calendario y alertas."""

from django.apps import AppConfig


class CalendarioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.calendario"
    verbose_name = "Calendario"
