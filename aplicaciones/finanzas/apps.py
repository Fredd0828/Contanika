"""Configuración de la aplicación del módulo 6: honorarios, cartera y cuentas de cobro."""

from django.apps import AppConfig


class FinanzasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.finanzas"
    verbose_name = "Honorarios, cartera y cuentas de cobro"
