"""
Modelos del módulo 2: calendario de vencimientos y alertas automáticas.

Cubre los vencimientos nacionales de la DIAN (calculados desde la tabla de
referencia oficial), los distritales y municipales (registro manual), los
vencimientos originados en tareas del Kanban, las alertas configurables y
las anotaciones libres por fecha.
"""

from django.db import models


class TablaReferenciaDian(models.Model):
    """
    Calendario oficial de la DIAN por grupo de NIT.

    El Administrador carga y actualiza esta tabla cada vez que la DIAN
    publica el calendario del período siguiente; con ella el sistema calcula
    automáticamente la fecha de vencimiento de cada cliente.
    """

    id_referencia = models.AutoField(primary_key=True)
    tipo_obligacion = models.CharField(max_length=40)
    grupo_nit = models.CharField(max_length=10)
    fecha_vencimiento = models.DateField()
    periodo_gravable = models.CharField(max_length=10)

    class Meta:
        db_table = "tabla_referencia_dian"
        verbose_name = "referencia DIAN"
        verbose_name_plural = "tabla de referencia DIAN"
        ordering = ["periodo_gravable", "tipo_obligacion", "grupo_nit"]
        constraints = [
            models.UniqueConstraint(
                fields=["tipo_obligacion", "grupo_nit", "periodo_gravable"],
                name="unico_referencia_dian",
            ),
        ]

    def __str__(self):
        return f"{self.tipo_obligacion} - NIT {self.grupo_nit} - {self.fecha_vencimiento}"


class Vencimiento(models.Model):
    """
    Vencimiento tributario nacional, distrital/municipal o de tarea marcada.

    Los vencimientos nacionales se generan desde la tabla de referencia DIAN y
    quedan con estado de validación 'Pendiente de validar'; los distritales y
    municipales se registran manualmente. La fecha siempre es editable.
    """

    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    PRESENTADA = "Presentada"
    OPCIONES_ESTADO_PRESENTACION = [
        (PENDIENTE, PENDIENTE),
        (EN_PROGRESO, EN_PROGRESO),
        (PRESENTADA, PRESENTADA),
    ]

    PENDIENTE_VALIDAR = "Pendiente de validar"
    VALIDADO = "Validado"
    OPCIONES_ESTADO_VALIDACION = [
        (PENDIENTE_VALIDAR, PENDIENTE_VALIDAR),
        (VALIDADO, VALIDADO),
    ]

    NACIONAL = "Nacional"
    DISTRITAL = "Distrital"
    MUNICIPAL = "Municipal"
    OPCIONES_AMBITO = [(NACIONAL, NACIONAL), (DISTRITAL, DISTRITAL), (MUNICIPAL, MUNICIPAL)]

    id_vencimiento = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        db_column="id_cliente",
        related_name="vencimientos",
    )
    tipo_obligacion = models.CharField(max_length=40)
    ambito = models.CharField(max_length=20, choices=OPCIONES_AMBITO, default=NACIONAL)
    municipio = models.CharField(max_length=60, blank=True)
    fecha_vencimiento = models.DateField()
    # Solo se llena en los vencimientos nacionales automáticos (copiado de
    # TablaReferenciaDian.periodo_gravable), para poder recalcular sin
    # duplicar cuando el Administrador corrige una fecha y vuelve a cargar
    # la tabla DIAN. Vacío en vencimientos manuales o generados por tarea.
    periodo_gravable = models.CharField(max_length=10, blank=True, default="")
    responsable = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.SET_NULL,
        db_column="id_usuario_responsable",
        related_name="vencimientos_asignados",
        null=True,
        blank=True,
    )
    estado_presentacion = models.CharField(
        max_length=20,
        choices=OPCIONES_ESTADO_PRESENTACION,
        default=PENDIENTE,
    )
    estado_validacion = models.CharField(
        max_length=20,
        choices=OPCIONES_ESTADO_VALIDACION,
        blank=True,
        default="",
    )
    tarea = models.ForeignKey(
        "tareas.Tarea",
        on_delete=models.SET_NULL,
        db_column="id_tarea",
        related_name="vencimientos",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "vencimiento"
        verbose_name = "vencimiento"
        verbose_name_plural = "vencimientos"
        ordering = ["fecha_vencimiento"]
        indexes = [
            models.Index(fields=["fecha_vencimiento"], name="idx_vencimiento_fecha"),
            models.Index(fields=["cliente", "fecha_vencimiento"], name="idx_vencimiento_cliente"),
        ]

    def __str__(self):
        return f"{self.cliente.nombre_razon_social} - {self.tipo_obligacion} ({self.fecha_vencimiento})"

    @property
    def es_automatico_dian(self):
        """Indica si el vencimiento fue calculado desde la tabla de referencia DIAN."""
        return self.tarea_id is None and self.ambito == self.NACIONAL


class ConfiguracionAlerta(models.Model):
    """Alerta automática configurada para un vencimiento, con su anticipación y canal."""

    CORREO = "Correo"
    WHATSAPP = "WhatsApp"
    NOTIFICACION = "Notificación interna"
    OPCIONES_CANAL = [(CORREO, CORREO), (WHATSAPP, WHATSAPP), (NOTIFICACION, NOTIFICACION)]

    id_alerta = models.AutoField(primary_key=True)
    vencimiento = models.ForeignKey(
        Vencimiento,
        on_delete=models.CASCADE,
        db_column="id_vencimiento",
        related_name="alertas",
    )
    dias_anticipacion = models.PositiveIntegerField(default=3)
    canal = models.CharField(max_length=20, choices=OPCIONES_CANAL, default=NOTIFICACION)

    class Meta:
        db_table = "configuracion_alerta"
        verbose_name = "configuración de alerta"
        verbose_name_plural = "configuraciones de alertas"
        ordering = ["vencimiento", "dias_anticipacion"]

    def __str__(self):
        return f"{self.canal} con {self.dias_anticipacion} días de anticipación"


class AnotacionCalendario(models.Model):
    """Anotación libre por fecha, no asociada a un cliente, con visibilidad configurable."""

    PRIVADA = "Privada"
    EQUIPO = "Equipo completo"
    POR_ROL = "Por rol"
    POR_ETIQUETA = "Por etiqueta"
    OPCIONES_VISIBILIDAD = [
        (PRIVADA, PRIVADA),
        (EQUIPO, EQUIPO),
        (POR_ROL, POR_ROL),
        (POR_ETIQUETA, POR_ETIQUETA),
    ]

    id_anotacion_cal = models.AutoField(primary_key=True)
    fecha = models.DateField()
    contenido = models.TextField()
    autor = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.PROTECT,
        db_column="id_usuario_autor",
        related_name="anotaciones_calendario",
    )
    visibilidad = models.CharField(max_length=20, choices=OPCIONES_VISIBILIDAD, default=EQUIPO)

    class Meta:
        db_table = "anotacion_calendario"
        verbose_name = "anotación de calendario"
        verbose_name_plural = "anotaciones de calendario"
        ordering = ["fecha", "id_anotacion_cal"]

    def __str__(self):
        return f"Anotación del {self.fecha}"


class AnotacionCalendarioDestinatario(models.Model):
    """Usuario etiquetado en una anotación de calendario con visibilidad restringida."""

    id_destinatario = models.AutoField(primary_key=True)
    anotacion_calendario = models.ForeignKey(
        AnotacionCalendario,
        on_delete=models.CASCADE,
        db_column="id_anotacion_cal",
        related_name="destinatarios",
    )
    usuario = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.CASCADE,
        db_column="id_usuario",
        related_name="anotaciones_calendario_etiquetadas",
    )

    class Meta:
        db_table = "anotacion_calendario_destinatario"
        verbose_name = "destinatario de anotación"
        verbose_name_plural = "destinatarios de anotaciones"
        constraints = [
            models.UniqueConstraint(
                fields=["anotacion_calendario", "usuario"],
                name="unico_anotacion_destinatario",
            ),
        ]

    def __str__(self):
        return f"{self.usuario.nombre} en anotación {self.anotacion_calendario_id}"
