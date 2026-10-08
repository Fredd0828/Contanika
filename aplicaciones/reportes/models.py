"""
Modelos del módulo 10: reportes y análisis.

Catálogo de los seis reportes del sistema, la habilitación de cada uno
por rol, que el Administrador configura de forma individual, y el registro
de las descargas.
"""

from django.db import models


class Reporte(models.Model):
    """Catálogo de los reportes disponibles en el módulo de análisis."""

    CLIENTES = "Clientes"
    VENCIMIENTOS = "Vencimientos tributarios"
    CARTERA = "Cartera"
    CUENTAS_COBRO = "Cuentas de cobro"
    TAREAS = "Tareas del Kanban"
    INGRESOS = "Ingresos mensuales del despacho"

    OPCIONES_REPORTE = [
        (CLIENTES, CLIENTES),
        (VENCIMIENTOS, VENCIMIENTOS),
        (CARTERA, CARTERA),
        (CUENTAS_COBRO, CUENTAS_COBRO),
        (TAREAS, TAREAS),
        (INGRESOS, INGRESOS),
    ]

    id_reporte = models.AutoField(primary_key=True)
    nombre_reporte = models.CharField(max_length=60, unique=True, choices=OPCIONES_REPORTE)
    modulo_origen = models.CharField(max_length=40)

    class Meta:
        db_table = "reporte"
        verbose_name = "reporte"
        verbose_name_plural = "reportes"
        ordering = ["id_reporte"]

    def __str__(self):
        return self.nombre_reporte


class PermisoReporteRol(models.Model):
    """Habilitación de cada reporte individual por rol."""

    id_permiso_reporte = models.AutoField(primary_key=True)
    reporte = models.ForeignKey(
        Reporte,
        on_delete=models.CASCADE,
        db_column="id_reporte",
        related_name="permisos_rol",
    )
    rol = models.ForeignKey(
        "seguridad.Rol",
        on_delete=models.CASCADE,
        db_column="id_rol",
        related_name="permisos_reporte",
    )
    habilitado = models.BooleanField(default=True)

    class Meta:
        db_table = "permiso_reporte_rol"
        verbose_name = "permiso de reporte por rol"
        verbose_name_plural = "permisos de reportes por rol"
        constraints = [
            models.UniqueConstraint(fields=["reporte", "rol"], name="unico_reporte_rol"),
        ]

    def __str__(self):
        return f"{self.rol.nombre_rol} - {self.reporte.nombre_reporte}: {self.habilitado}"


class DescargaReporte(models.Model):
    """
    Registro de cada descarga de un reporte (HU028-5): qué reporte, quién, cuándo,
    en qué formato y con qué filtros. Tabla agregada en el Módulo 10.
    """

    EXCEL = "Excel"
    PDF = "PDF"
    OPCIONES_FORMATO = [(EXCEL, EXCEL), (PDF, PDF)]

    id_descarga = models.AutoField(primary_key=True)
    reporte = models.ForeignKey(
        Reporte,
        on_delete=models.PROTECT,
        db_column="id_reporte",
        related_name="descargas",
    )
    usuario = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.PROTECT,
        db_column="id_usuario",
        related_name="descargas_reporte",
    )
    formato = models.CharField(max_length=10, choices=OPCIONES_FORMATO)
    filtros = models.TextField(blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "descarga_reporte"
        verbose_name = "descarga de reporte"
        verbose_name_plural = "descargas de reportes"
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"{self.reporte.nombre_reporte} ({self.formato}) - {self.usuario.nombre}"
