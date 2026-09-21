"""Configuración de la aplicación del módulo 1: gestión de clientes."""

from django.apps import AppConfig


class ClientesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.clientes"
    verbose_name = "Gestión de clientes"
