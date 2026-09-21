"""
Configuración del entorno local de desarrollo.

Usa la base de datos PostgreSQL instalada en el equipo del aprendiz y muestra
los correos por consola en lugar de enviarlos realmente.
"""

from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# En desarrollo los correos se imprimen en la consola para poder revisarlos.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Herramientas de depuración que solo aplican en local.
INTERNAL_IPS = ["127.0.0.1"]
