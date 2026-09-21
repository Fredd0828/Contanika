"""Configuración de la aplicación de equipo, roles y seguridad."""

from django.apps import AppConfig


class SeguridadConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.seguridad"
    verbose_name = "Seguridad y equipo"
