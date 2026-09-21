"""
Modelos del módulo 5: hallazgos y revisiones contables.

Registra los hallazgos, revisiones periódicas, observaciones e
inconsistencias detectadas en el trabajo contable de cada cliente, con su
nivel de prioridad, estado y observación de cierre.
"""

from django.db import models


class Hallazgo(models.Model):
    """Hallazgo o revisión registrada para un cliente del despacho."""

    ABIERTO = "Abierto"
    EN_PROCESO = "En proceso"
    CERRADO = "Cerrado"
    PENDIENTE_CLIENTE = "Pendiente cliente"
    OPCIONES_ESTADO = [
        (ABIERTO, ABIERTO),
        (EN_PROCESO, EN_PROCESO),
        (CERRADO, CERRADO),
        (PENDIENTE_CLIENTE, PENDIENTE_CLIENTE),
    ]

    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"
    OPCIONES_PRIORIDAD = [(ALTA, ALTA), (MEDIA, MEDIA), (BAJA, BAJA)]

    id_hallazgo = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        db_column="id_cliente",
        related_name="hallazgos",
    )
    tipo_hallazgo = models.CharField(max_length=40)
    fecha_inicio_periodo = models.DateField()
    fecha_fin_periodo = models.DateField()
    responsable = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.PROTECT,
        db_column="id_usuario_responsable",
        related_name="hallazgos_asignados",
        null=True,
        blank=True,
    )
    prioridad = models.CharField(max_length=10, choices=OPCIONES_PRIORIDAD, default=MEDIA)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=OPCIONES_ESTADO, default=ABIERTO)
    observacion_cierre = models.TextField(blank=True)

    class Meta:
        db_table = "hallazgo"
        verbose_name = "hallazgo"
        verbose_name_plural = "hallazgos"
        ordering = ["-fecha_inicio_periodo", "prioridad"]
        indexes = [
            models.Index(fields=["estado"], name="idx_hallazgo_estado"),
            models.Index(fields=["cliente", "estado"], name="idx_hallazgo_cliente"),
        ]

    def __str__(self):
        return f"{self.tipo_hallazgo} - {self.cliente.nombre_razon_social} ({self.estado})"

    def cerrar(self, observacion):
        """
        Cierra el hallazgo guardando la observación de cierre.

        El módulo exige que al pasar a estado cerrado quede registrada la
        observación con la que se resolvió el hallazgo.
        """
        self.estado = self.CERRADO
        self.observacion_cierre = observacion
        self.save(update_fields=["estado", "observacion_cierre"])
