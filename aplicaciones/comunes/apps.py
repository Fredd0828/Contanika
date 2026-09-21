"""Configuración de la aplicación de modelos y utilidades compartidas."""

from django.apps import AppConfig


class ComunesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.comunes"
    verbose_name = "Comunes"
