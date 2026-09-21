"""Configuración de la aplicación del módulo 4: documentos y certificados."""

from django.apps import AppConfig


class DocumentosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.documentos"
    verbose_name = "Expedición de documentos y certificados"
