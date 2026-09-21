"""Configuración de la aplicación del módulo 3: tablero de tareas Kanban."""

from django.apps import AppConfig


class TareasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.tareas"
    verbose_name = "Tablero de tareas Kanban"
