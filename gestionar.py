#!/usr/bin/env python
"""Utilidad de línea de comandos de Django para tareas administrativas del proyecto Contanika."""

import os
import sys


def modulo_de_configuracion(entorno):
    """
    Devuelve el módulo de configuración que corresponde a la variable `ENTORNO`.

    Solo `produccion` activa la configuración de producción, sin importar las
    mayúsculas ni los espacios; cualquier otro valor usa la local.
    """
    if entorno.strip().lower() == "produccion":
        return "config.settings.produccion"
    return "config.settings.local"


def main():
    """Ejecuta los comandos administrativos de Django."""
    try:
        from decouple import config
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No fue posible importar Django. Verifique que está instalado y que "
            "el entorno virtual está activado (source .venv/bin/activate)."
        ) from exc
    # `ENTORNO` vive en `.env`: así el cron y los comandos manuales usan siempre
    # la misma configuración, sin tener que exportar variables en cada uno.
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", modulo_de_configuracion(config("ENTORNO", default="local"))
    )
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
