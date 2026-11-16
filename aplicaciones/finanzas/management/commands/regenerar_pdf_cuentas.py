"""
Vuelve a generar el PDF guardado de las cuentas de cobro con el diseño actual.

Sirve cuando cambia la presentación de los PDF: las cuentas ya generadas
conservan el archivo viejo hasta que algo las regenera (por ejemplo, un
abono). Los datos de la cuenta no cambian; solo se rehace su archivo.

Los certificados del Módulo 4 no se regeneran: el documento no guarda con
qué firma se expidió, y rehacerlo con otra sería alterar un documento firmado.

Uso:
    python gestionar.py regenerar_pdf_cuentas            # solo muestra cuántas son
    python gestionar.py regenerar_pdf_cuentas --aplicar  # las regenera
"""

from django.core.management.base import BaseCommand

from aplicaciones.finanzas.models import CuentaCobro
from aplicaciones.finanzas.servicios import actualizar_pdf_cuenta_cobro


class Command(BaseCommand):
    help = "Regenera con el diseño actual el PDF guardado de las cuentas de cobro."

    def add_arguments(self, parser):
        parser.add_argument(
            "--aplicar",
            action="store_true",
            help="Regenera los archivos. Sin esta opción solo informa cuántas cuentas hay.",
        )

    def handle(self, *args, **opciones):
        cuentas = CuentaCobro.objects.select_related("cliente").order_by("pk")
        total = cuentas.count()
        if not opciones["aplicar"]:
            self.stdout.write(
                f"Hay {total} cuenta(s) de cobro. Nada cambió: use --aplicar para regenerar sus PDF."
            )
            return

        regeneradas, fallidas = 0, []
        for cuenta in cuentas.iterator():
            try:
                actualizar_pdf_cuenta_cobro(cuenta)
            except Exception as error:  # noqa: BLE001 - una cuenta dañada no detiene las demás
                fallidas.append((cuenta.pk, error))
            else:
                regeneradas += 1
        self.stdout.write(self.style.SUCCESS(f"PDF regenerados: {regeneradas} de {total}."))
        for pk, error in fallidas:
            self.stdout.write(self.style.WARNING(f"Cuenta {pk}: no se pudo regenerar ({error})."))
