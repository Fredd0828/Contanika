#!/usr/bin/env python
"""Utilidad de línea de comandos de Django para tareas administrativas del proyecto Contanika."""

import os
import sys


def main():
    """Ejecuta los comandos administrativos de Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No fue posible importar Django. Verifique que está instalado y que "
            "el entorno virtual está activado (source .venv/bin/activate)."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
