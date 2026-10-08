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
from aplicaciones.documentos.models import CampoPlantilla, Plantilla
from aplicaciones.finanzas.models import ConceptoFacturable, ConfiguracionCobro, MetodoPago
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
    {
        "nombre": "Certificación de ingresos para independientes",
        "texto": (
            "El suscrito contador certifica que {{ cliente }}, identificado con "
            "{{ tipo_documento_cliente }} No. {{ identificacion_cliente }}, ejerce la "
            "actividad económica de {{ actividad_economica }} de manera independiente.\n\n"
            "Para el período {{ periodo }}, se certifica un ingreso de "
            "$ {{ valor_del_ingreso_certificado }}, por concepto de {{ concepto }}.\n\n"
            "Esta certificación se expide a solicitud del interesado en "
            "{{ ciudad_despacho }}, el {{ fecha_expedicion }}."
        ),
        "campos": [
            ("Actividad económica", CampoPlantilla.SIMPLE),
            ("Valor del ingreso certificado", CampoPlantilla.SIMPLE),
            ("Concepto", CampoPlantilla.SIMPLE),
        ],
    },
    {
        "nombre": "Certificado de ingresos y retenciones (Art. 378 ET)",
        "texto": (
            "Certificado de ingresos y retenciones - Artículo 378 del Estatuto "
            "Tributario, período gravable {{ periodo }}.\n\n"
            "{{ nombre_despacho }} certifica, como agente retenedor, que durante el "
            "período {{ periodo }} efectuó pagos a {{ nombre_del_asalariado }}, "
            "identificado con cédula No. {{ identificacion_del_asalariado }}.\n\n"
            "Agente retenedor: {{ cliente }}, NIT {{ identificacion_cliente }}, con "
            "dirección {{ direccion_del_agente_retenedor }}.\n\n"
            "Valor de los pagos o abonos en cuenta: $ {{ valor_de_los_pagos_o_abonos }}, "
            "por concepto de {{ concepto }}. Monto de la retención practicada: "
            "$ {{ monto_de_la_retencion }}.\n\n"
            "La retención fue consignada en {{ ciudad_donde_se_consigno_la_retencion }}.\n\n"
            "Se expide el presente certificado en {{ ciudad_despacho }}, el "
            "{{ fecha_expedicion }}."
        ),
        "campos": [
            ("Ciudad donde se consignó la retención", CampoPlantilla.SIMPLE),
            ("Nombre del asalariado", CampoPlantilla.SIMPLE),
            ("Identificación del asalariado", CampoPlantilla.SIMPLE),
            ("Dirección del agente retenedor", CampoPlantilla.SIMPLE),
            ("Valor de los pagos o abonos", CampoPlantilla.SIMPLE),
            ("Concepto", CampoPlantilla.SIMPLE),
            ("Monto de la retención", CampoPlantilla.SIMPLE),
        ],
    },
    {
        "nombre": "Certificado de composición accionaria",
        "texto": (
            "Se certifica que la composición accionaria de {{ cliente }}, "
            "identificada con NIT {{ identificacion_cliente }}, con corte a "
            "{{ periodo }}, es la siguiente:\n\n"
            "{% for fila in filas_repetibles %}- {{ fila.nombre_del_accionista }}: "
            "{{ fila.porcentaje_de_participacion }}%\n{% endfor %}\n"
            "Se expide la presente certificación en {{ ciudad_despacho }}, el "
            "{{ fecha_expedicion }}."
        ),
        "campos": [
            ("Nombre del accionista", CampoPlantilla.REPETIBLE),
            ("Porcentaje de participación", CampoPlantilla.REPETIBLE),
        ],
    },
    {
        "nombre": "Certificado de patrimonio",
        "texto": (
            "Se certifica que, con corte a {{ periodo }}, {{ cliente }}, identificado "
            "con {{ tipo_documento_cliente }} No. {{ identificacion_cliente }}, "
            "presenta el siguiente patrimonio:\n\n"
            "Valor del patrimonio: $ {{ valor_del_patrimonio }}\n"
            "Total de activos: $ {{ total_de_activos }}\n"
            "Total de pasivos: $ {{ total_de_pasivos }}\n\n"
            "Esta certificación se expide con base en {{ base_de_la_certificacion }}, "
            "en {{ ciudad_despacho }}, el {{ fecha_expedicion }}."
        ),
        "campos": [
            ("Valor del patrimonio", CampoPlantilla.SIMPLE),
            ("Total de activos", CampoPlantilla.SIMPLE),
            ("Total de pasivos", CampoPlantilla.SIMPLE),
            ("Base de la certificación", CampoPlantilla.SIMPLE),
        ],
    },
    {
        "nombre": "Certificado de dependiente económico",
        "texto": (
            "Se certifica que {{ nombre_del_dependiente_economico }}, identificado "
            "con cédula No. {{ identificacion_del_dependiente_economico }}, es "
            "dependiente económico de {{ cliente }}, identificado con "
            "{{ tipo_documento_cliente }} No. {{ identificacion_cliente }}, en calidad "
            "de {{ relacion_o_parentesco }}, para el año gravable {{ periodo }}.\n\n"
            "Se certifica que el dependiente económico cumple los requisitos "
            "establecidos en el Estatuto Tributario para ser considerado como tal.\n\n"
            "Se expide la presente certificación en {{ ciudad_despacho }}, el "
            "{{ fecha_expedicion }}."
        ),
        "campos": [
            ("Nombre del dependiente económico", CampoPlantilla.SIMPLE),
            ("Identificación del dependiente económico", CampoPlantilla.SIMPLE),
            ("Relación o parentesco", CampoPlantilla.SIMPLE),
        ],
    },
    {
        "nombre": "Certificación de no obligación a declarar renta",
        "texto": (
            "Se certifica que {{ cliente }}, identificado con "
            "{{ tipo_documento_cliente }} No. {{ identificacion_cliente }}, para el "
            "año gravable {{ periodo }}, no se encuentra obligado a declarar renta, "
            "de acuerdo con los siguientes valores:\n\n"
            "Ingresos brutos: $ {{ ingresos_brutos }}\n"
            "Patrimonio bruto: $ {{ patrimonio_bruto }}\n"
            "Consignaciones, compras y consumos del período: "
            "$ {{ consignaciones_compras_y_consumos_del_periodo }}\n\n"
            "Se certifica que estos valores no superan los topes vigentes "
            "establecidos por la DIAN para estar obligado a declarar renta.\n\n"
            "Se expide la presente certificación en {{ ciudad_despacho }}, el "
            "{{ fecha_expedicion }}."
        ),
        "campos": [
            ("Ingresos brutos", CampoPlantilla.SIMPLE),
            ("Patrimonio bruto", CampoPlantilla.SIMPLE),
            ("Consignaciones, compras y consumos del período", CampoPlantilla.SIMPLE),
        ],
    },
]

REPORTES = [
    (Reporte.CLIENTES, "Gestión de clientes"),
    (Reporte.VENCIMIENTOS, "Calendario"),
    (Reporte.CARTERA, "Honorarios y cartera"),
    (Reporte.CUENTAS_COBRO, "Honorarios y cartera"),
    (Reporte.TAREAS, "Tablero Kanban"),
    (Reporte.INGRESOS, "Honorarios y cartera"),
]

# Lo que el Contador Junior no ve al crear el sistema (el Administrador puede habilitarlo).
MODULOS_SIN_JUNIOR = (Modulo.MOD06_FINANZAS, Modulo.SEC_PANEL)
REPORTES_SIN_JUNIOR = (Reporte.CARTERA, Reporte.CUENTAS_COBRO, Reporte.INGRESOS)


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
        """Habilita los módulos y reportes de los tres roles, salvo lo financiero del Junior.

        El Contador Junior empieza sin el módulo de Honorarios y sin los
        reportes de cartera, cuentas de cobro e ingresos (decisión del usuario,
        7-oct-2026). Solo se fija al crear la fila: el Administrador puede
        cambiarlo después desde el módulo 8 y Reportes → Visibilidad por rol
        (RQF031), y el comando no lo pisa.
        """
        for rol in Rol.objects.all():
            es_junior = rol.nombre_rol == Rol.CONTADOR_JUNIOR
            for modulo in Modulo.objects.all():
                PermisoRolModulo.objects.get_or_create(
                    rol=rol,
                    modulo=modulo,
                    defaults={"habilitado": not (es_junior and modulo.codigo_modulo in MODULOS_SIN_JUNIOR)},
                )
            for reporte in Reporte.objects.all():
                PermisoReporteRol.objects.get_or_create(
                    rol=rol,
                    reporte=reporte,
                    defaults={
                        "habilitado": not (es_junior and reporte.nombre_reporte in REPORTES_SIN_JUNIOR)
                    },
                )

    def _crear_configuracion(self):
        ConfiguracionDespacho.objects.get_or_create(
            pk=1,
            defaults={
                "nombre_despacho": "Befrec Y Asociados SAS",
                "ciudad": "Bogotá D.C.",
            },
        )
        # Cobro automático del Módulo 6: se crea desactivado, lo activa el Administrador.
        ConfiguracionCobro.obtener()

    def _crear_catalogos(self):
        for nombre in TIPOS_SERVICIO:
            TipoServicio.objects.get_or_create(nombre_servicio=nombre)
        for nombre in METODOS_PAGO:
            MetodoPago.objects.get_or_create(nombre_metodo=nombre)
        for nombre in CONCEPTOS_FACTURABLES:
            ConceptoFacturable.objects.get_or_create(nombre_concepto=nombre)

    def _crear_plantillas(self):
        """
        Crea las 6 plantillas base con su texto predeterminado y sus campos.

        El texto predeterminado solo se fija al crear la plantilla: si el
        comando se vuelve a correr, no pisa el texto que el Administrador ya
        haya editado desde la gestión de plantillas.
        """
        for datos in PLANTILLAS_BASE:
            plantilla, _ = Plantilla.objects.get_or_create(
                nombre_plantilla=datos["nombre"],
                defaults={"tipo_documento": datos["nombre"], "texto_predeterminado": datos["texto"]},
            )
            for nombre_campo, tipo_campo in datos["campos"]:
                CampoPlantilla.objects.get_or_create(
                    plantilla=plantilla,
                    nombre_campo=nombre_campo,
                    defaults={
                        "tipo_campo": tipo_campo,
                        "es_repetible": tipo_campo == CampoPlantilla.REPETIBLE,
                    },
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
