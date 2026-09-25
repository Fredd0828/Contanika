"""
Proceso automático de cobro del Módulo 6.

Pensado para ejecutarse con cron cada 15 minutos, por ejemplo:

    */15 * * * * cd /ruta/codigo && .venv/bin/python gestionar.py procesar_cobros

Marca las cuentas vencidas, genera el cobro mensual automático, programa los
recordatorios de pago y despacha los envíos cuya hora ya llegó. Es idempotente.
"""

from django.core.management.base import BaseCommand

from aplicaciones.finanzas import servicios


class Command(BaseCommand):
    help = "Procesa el cobro automático: vencidas, cobro mensual, recordatorios y envíos programados."

    def handle(self, *args, **opciones):
        resumen = servicios.procesar_cobros()
        for clave, valor in resumen.items():
            self.stdout.write(f"{clave.replace('_', ' ').capitalize()}: {valor}")
        self.stdout.write(self.style.SUCCESS("Proceso de cobro terminado."))
