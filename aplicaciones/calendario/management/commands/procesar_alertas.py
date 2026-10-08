"""
Proceso automático de alertas del Módulo 2.

Pensado para ejecutarse con cron, por ejemplo una vez por hora:

    0 * * * * cd /ruta/codigo && .venv/bin/python gestionar.py procesar_alertas

Envía por correo las alertas de vencimientos cuyo aviso ya llegó y deja
registro de lo enviado. Es idempotente: no repite una alerta ya enviada.
"""

from django.core.management.base import BaseCommand

from aplicaciones.calendario import servicios


class Command(BaseCommand):
    help = "Envía las alertas de vencimientos cuya fecha de aviso ya llegó."

    def handle(self, *args, **opciones):
        resumen = servicios.procesar_alertas()
        for clave, valor in resumen.items():
            self.stdout.write(f"{clave.replace('_', ' ').capitalize()}: {valor}")
        self.stdout.write(self.style.SUCCESS("Proceso de alertas terminado."))
