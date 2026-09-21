"""Configuración de la aplicación del módulo 9: expediente y bitácora."""

from django.apps import AppConfig


class ExpedienteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.expediente"
    verbose_name = "Expediente y bitácora por cliente"
