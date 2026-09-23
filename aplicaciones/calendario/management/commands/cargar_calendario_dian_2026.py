"""
Carga el calendario oficial DIAN 2026 en la tabla de referencia.

El comando es idempotente: si un registro ya existe (mismo tipo de obligación,
grupo de NIT y período gravable) actualiza la fecha de vencimiento; si no
existe, lo crea. Esto permite corregir fechas ejecutando el comando de nuevo
sin duplicar filas.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from aplicaciones.calendario.datos_dian_2026 import generar_registros_dian_2026
from aplicaciones.calendario.models import TablaReferenciaDian


class Command(BaseCommand):
    help = "Carga o actualiza la tabla de referencia del calendario DIAN 2026."

    @transaction.atomic
    def handle(self, *args, **options):
        registros = generar_registros_dian_2026()
        creados = 0
        actualizados = 0

        for datos in registros:
            _, creado = TablaReferenciaDian.objects.update_or_create(
                tipo_obligacion=datos["tipo_obligacion"],
                grupo_nit=datos["grupo_nit"],
                periodo_gravable=datos["periodo_gravable"],
                defaults={"fecha_vencimiento": datos["fecha_vencimiento"]},
            )
            if creado:
                creados += 1
            else:
                actualizados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Calendario DIAN 2026 cargado: {creados} registros creados, "
                f"{actualizados} actualizados ({creados + actualizados} en total)."
            )
        )
