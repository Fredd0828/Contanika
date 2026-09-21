"""
Carga los datos iniciales del sistema Contanika.

Crea los tres roles, los diez módulos, los seis reportes, sus permisos por
rol, la configuración del despacho y los catálogos base (tipos de servicio,
métodos de pago, conceptos facturables y las seis plantillas de documento).
El comando es idempotente: puede ejecutarse varias veces sin duplicar datos.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from aplicaciones.clientes.models import TipoServicio
from aplicaciones.documentos.models import Plantilla
from aplicaciones.finanzas.models import ConceptoFacturable, MetodoPago
from aplicaciones.reportes.models import PermisoReporteRol, Reporte
from aplicaciones.seguridad.models import (
    ConfiguracionDespacho,
    Modulo,
    PermisoRolModulo,
    Rol,
    Usuario,
)

TIPOS_SERVICIO = [
    "Declaración de renta",
    "Declaración de IVA",
    "Retención en la fuente",
    "Contabilidad mensual",
    "Nómina",
    "Información exógena",
    "Medios magnéticos",
    "Industria y comercio (ICA)",
]

METODOS_PAGO = ["Transferencia", "Consignación", "Efectivo", "Nequi", "Daviplata"]

CONCEPTOS_FACTURABLES = [
    "Contabilidad mensual",
    "Nómina",
    "Declaración de renta",
    "Declaración de IVA",
    "Revisoría fiscal",
]

PLANTILLAS_BASE = [
    "Certificación de ingresos para independientes",
    "Certificado de ingresos y retenciones (Art. 378 ET)",
    "Certificado de composición accionaria",
    "Certificado de patrimonio",
    "Certificado de dependiente económico",
    "Certificación de no obligación a declarar renta",
]

REPORTES = [
    (Reporte.CLIENTES, "Gestión de clientes"),
    (Reporte.VENCIMIENTOS, "Calendario"),
    (Reporte.CARTERA, "Honorarios y cartera"),
    (Reporte.CUENTAS_COBRO, "Honorarios y cartera"),
    (Reporte.TAREAS, "Tablero Kanban"),
    (Reporte.INGRESOS, "Honorarios y cartera"),
]


class Command(BaseCommand):
    help = "Crea roles, módulos, reportes, permisos y catálogos base del sistema."

    def add_arguments(self, parser):
        parser.add_argument(
            "--correo-admin",
            help="Correo del superusuario Administrador a crear (opcional).",
        )
        parser.add_argument(
            "--nombre-admin",
            default="Administrador",
            help="Nombre del superusuario Administrador a crear (opcional).",
        )
        parser.add_argument(
            "--clave-admin",
            help="Contraseña del superusuario Administrador a crear (opcional).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self._crear_roles()
        self._crear_modulos()
        self._crear_reportes()
        self._crear_permisos()
        self._crear_configuracion()
        self._crear_catalogos()
        self._crear_plantillas()
        self._crear_admin(opciones=options)
        self.stdout.write(self.style.SUCCESS("Datos iniciales cargados correctamente."))

    # -----------------------------------------------------------
    # Métodos de apoyo
    # -----------------------------------------------------------
    def _crear_roles(self):
        for nombre in Rol.OPCIONES_ROL:
            Rol.objects.get_or_create(nombre_rol=nombre[0])

    def _crear_modulos(self):
        for codigo, nombre in Modulo.OPCIONES_CODIGO:
            Modulo.objects.get_or_create(codigo_modulo=codigo, defaults={"nombre_modulo": nombre})

    def _crear_reportes(self):
        for nombre, origen in REPORTES:
            Reporte.objects.get_or_create(nombre_reporte=nombre, defaults={"modulo_origen": origen})

    def _crear_permisos(self):
        """Habilita todos los módulos y reportes para los tres roles.

        El Administrador puede inhabilitar módulos o reportes individuales
        después, desde la configuración del módulo 8 (RQF031).
        """
        for rol in Rol.objects.all():
            for modulo in Modulo.objects.all():
                PermisoRolModulo.objects.get_or_create(
                    rol=rol,
                    modulo=modulo,
                    defaults={"habilitado": True},
                )
            for reporte in Reporte.objects.all():
                PermisoReporteRol.objects.get_or_create(
                    rol=rol,
                    reporte=reporte,
                    defaults={"habilitado": True},
                )

    def _crear_configuracion(self):
        ConfiguracionDespacho.objects.get_or_create(
            pk=1,
            defaults={
                "nombre_despacho": "Befrec Y Asociados SAS",
                "ciudad": "Bogotá D.C.",
            },
        )

    def _crear_catalogos(self):
        for nombre in TIPOS_SERVICIO:
            TipoServicio.objects.get_or_create(nombre_servicio=nombre)
        for nombre in METODOS_PAGO:
            MetodoPago.objects.get_or_create(nombre_metodo=nombre)
        for nombre in CONCEPTOS_FACTURABLES:
            ConceptoFacturable.objects.get_or_create(nombre_concepto=nombre)

    def _crear_plantillas(self):
        for nombre in PLANTILLAS_BASE:
            Plantilla.objects.get_or_create(
                nombre_plantilla=nombre,
                defaults={"tipo_documento": nombre},
            )

    def _crear_admin(self, opciones):
        correo = opciones.get("correo_admin")
        clave = opciones.get("clave_admin")
        if not correo or not clave:
            return
        if Usuario.objects.filter(correo=correo).exists():
            self.stdout.write(f"El usuario {correo} ya existe; no se creó de nuevo.")
            return
        rol_admin = Rol.objects.get(nombre_rol=Rol.ADMINISTRADOR)
        Usuario.objects.create_superuser(
            correo=correo,
            nombre=opciones["nombre_admin"],
            password=clave,
            rol=rol_admin,
        )
        self.stdout.write(f"Superusuario {correo} creado.")
