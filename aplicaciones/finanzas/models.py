"""
Modelos del módulo 6: honorarios, cartera y cuentas de cobro.

Cubre la configuración del honorario por cliente, los catálogos de conceptos
facturables, cuentas bancarias y métodos de pago, la generación de cuentas
de cobro en PDF, su detalle de líneas de servicio y el registro de abonos
con trazabilidad de saldos.
"""

from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Honorario(models.Model):
    """Configuración del honorario de un cliente (fijo mensual o por servicio)."""

    FIJO_MENSUAL = "Fijo mensual"
    POR_SERVICIO = "Por servicio"
    OPCIONES_TIPO = [(FIJO_MENSUAL, FIJO_MENSUAL), (POR_SERVICIO, POR_SERVICIO)]

    id_honorario = models.AutoField(primary_key=True)
    cliente = models.OneToOneField(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        db_column="id_cliente",
        related_name="honorario",
    )
    tipo = models.CharField(max_length=20, choices=OPCIONES_TIPO, default=FIJO_MENSUAL)
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    usuario_actualizacion = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.SET_NULL,
        db_column="id_usuario_actualizacion",
        related_name="honorarios_actualizados",
        null=True,
        blank=True,
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "honorario"
        verbose_name = "honorario"
        verbose_name_plural = "honorarios"

    def __str__(self):
        return f"{self.cliente.nombre_razon_social}: ${self.monto} ({self.tipo})"


class HonorarioServicio(models.Model):
    """
    Monto del honorario por cada tipo de servicio del cliente (HU044).

    Solo aplica cuando el honorario es "Por servicio"; el monto total del
    honorario es la suma de estas líneas.
    """

    id_honorario_servicio = models.AutoField(primary_key=True)
    honorario = models.ForeignKey(
        Honorario,
        on_delete=models.CASCADE,
        db_column="id_honorario",
        related_name="servicios",
    )
    tipo_servicio = models.ForeignKey(
        "clientes.TipoServicio",
        on_delete=models.PROTECT,
        db_column="id_tipo_servicio",
        related_name="honorarios",
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "honorario_servicio"
        verbose_name = "honorario por servicio"
        verbose_name_plural = "honorarios por servicio"
        ordering = ["tipo_servicio__nombre_servicio"]
        constraints = [
            models.UniqueConstraint(fields=["honorario", "tipo_servicio"], name="unico_honorario_servicio"),
        ]

    def __str__(self):
        return f"{self.tipo_servicio}: ${self.monto}"


class ConceptoFacturable(models.Model):
    """Catálogo reutilizable de conceptos facturables definidos por el Administrador."""

    id_concepto = models.AutoField(primary_key=True)
    nombre_concepto = models.CharField(max_length=100, unique=True)
    valor_sugerido = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "concepto_facturable"
        verbose_name = "concepto facturable"
        verbose_name_plural = "conceptos facturables"
        ordering = ["nombre_concepto"]

    def __str__(self):
        return self.nombre_concepto


class CuentaBancaria(models.Model):
    """Cuenta bancaria del despacho disponible como destino de pago."""

    id_cuenta_bancaria = models.AutoField(primary_key=True)
    banco = models.CharField(max_length=60)
    tipo_cuenta = models.CharField(max_length=20)
    numero_cuenta = models.CharField(max_length=30)
    titular = models.CharField(max_length=150)

    class Meta:
        db_table = "cuenta_bancaria"
        verbose_name = "cuenta bancaria"
        verbose_name_plural = "cuentas bancarias"
        ordering = ["banco", "tipo_cuenta"]

    def __str__(self):
        return f"{self.banco} {self.tipo_cuenta} {self.numero_cuenta}"


class MetodoPago(models.Model):
    """Catálogo de métodos de pago aceptados por el despacho."""

    id_metodo_pago = models.AutoField(primary_key=True)
    nombre_metodo = models.CharField(max_length=40, unique=True)

    class Meta:
        db_table = "metodo_pago"
        verbose_name = "método de pago"
        verbose_name_plural = "métodos de pago"
        ordering = ["nombre_metodo"]

    def __str__(self):
        return self.nombre_metodo


class CuentaCobro(models.Model):
    """Cuenta de cobro generada en PDF y enviada a un cliente."""

    MENSUAL = "Mensual"
    BIMESTRAL = "Bimestral"
    TRIMESTRAL = "Trimestral"
    SEMESTRAL = "Semestral"
    ANUAL = "Anual"
    PERSONALIZADO = "Personalizado"
    OPCIONES_PERIODO = [
        (MENSUAL, MENSUAL),
        (BIMESTRAL, BIMESTRAL),
        (TRIMESTRAL, TRIMESTRAL),
        (SEMESTRAL, SEMESTRAL),
        (ANUAL, ANUAL),
        (PERSONALIZADO, PERSONALIZADO),
    ]

    PENDIENTE = "Pendiente"
    ENVIADA = "Enviada"
    FALLIDA = "Fallida"
    OPCIONES_ESTADO_ENVIO = [(PENDIENTE, PENDIENTE), (ENVIADA, ENVIADA), (FALLIDA, FALLIDA)]

    PAGO_PENDIENTE = "Pendiente"
    ABONADA = "Abonada"
    PAGADA = "Pagada"
    VENCIDA = "Vencida"
    OPCIONES_ESTADO_PAGO = [
        (PAGO_PENDIENTE, PAGO_PENDIENTE),
        (ABONADA, ABONADA),
        (PAGADA, PAGADA),
        (VENCIDA, VENCIDA),
    ]

    id_cuenta_cobro = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        db_column="id_cliente",
        related_name="cuentas_cobro",
    )
    honorario = models.ForeignKey(
        Honorario,
        on_delete=models.PROTECT,
        db_column="id_honorario",
        related_name="cuentas_cobro",
        null=True,
        blank=True,
    )
    periodo_facturado = models.CharField(max_length=20, choices=OPCIONES_PERIODO, default=MENSUAL)
    fecha_inicio_periodo = models.DateField(null=True, blank=True)
    fecha_fin_periodo = models.DateField(null=True, blank=True)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    cuenta_bancaria = models.ForeignKey(
        CuentaBancaria,
        on_delete=models.PROTECT,
        db_column="id_cuenta_bancaria",
        related_name="cuentas_cobro",
        null=True,
        blank=True,
    )
    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.PROTECT,
        db_column="id_metodo_pago",
        related_name="cuentas_cobro",
        null=True,
        blank=True,
    )
    fecha_vencimiento_pago = models.DateField()
    estado_envio = models.CharField(max_length=20, choices=OPCIONES_ESTADO_ENVIO, default=PENDIENTE)
    estado_pago = models.CharField(max_length=20, choices=OPCIONES_ESTADO_PAGO, default=PAGO_PENDIENTE)
    archivo = models.FileField(upload_to="cuentas_cobro/%Y/%m/", blank=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cuenta_cobro"
        verbose_name = "cuenta de cobro"
        verbose_name_plural = "cuentas de cobro"
        ordering = ["-fecha_generacion"]
        indexes = [
            models.Index(fields=["cliente", "estado_pago"], name="idx_cuenta_cobro_cliente"),
            models.Index(fields=["fecha_vencimiento_pago"], name="idx_cuenta_cobro_vencimiento"),
        ]

    def __str__(self):
        return f"Cuenta de cobro {self.id_cuenta_cobro} - {self.cliente.nombre_razon_social}"

    @property
    def total_abonado(self):
        """Suma de los abonos registrados contra la cuenta de cobro."""
        return self.abonos.aggregate(total=Sum("monto"))["total"] or 0

    @property
    def saldo_pendiente(self):
        """Saldo que aún debe pagar el cliente."""
        return self.valor_total - self.total_abonado

    @property
    def esta_en_mora(self):
        """Indica si la cuenta venció y todavía tiene saldo pendiente."""
        return self.saldo_pendiente > 0 and self.fecha_vencimiento_pago < timezone.localdate()


class CuentaCobroDetalle(models.Model):
    """Línea de servicio descrita dentro de una cuenta de cobro."""

    id_detalle_cobro = models.AutoField(primary_key=True)
    cuenta_cobro = models.ForeignKey(
        CuentaCobro,
        on_delete=models.CASCADE,
        db_column="id_cuenta_cobro",
        related_name="detalles",
    )
    concepto = models.ForeignKey(
        ConceptoFacturable,
        on_delete=models.SET_NULL,
        db_column="id_concepto",
        related_name="detalles_cobro",
        null=True,
        blank=True,
    )
    descripcion_linea = models.CharField(max_length=200)
    valor_linea = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "cuenta_cobro_detalle"
        verbose_name = "detalle de cuenta de cobro"
        verbose_name_plural = "detalles de cuentas de cobro"
        ordering = ["cuenta_cobro", "id_detalle_cobro"]

    def __str__(self):
        return self.descripcion_linea


class Abono(models.Model):
    """
    Pago o abono registrado contra una cuenta de cobro.

    Guarda el saldo anterior y el saldo resultante para conservar la
    trazabilidad completa de la cartera del despacho.
    """

    id_abono = models.AutoField(primary_key=True)
    cuenta_cobro = models.ForeignKey(
        CuentaCobro,
        on_delete=models.CASCADE,
        db_column="id_cuenta_cobro",
        related_name="abonos",
    )
    fecha = models.DateField(default=timezone.localdate)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.PROTECT,
        db_column="id_metodo_pago",
        related_name="abonos",
        null=True,
        blank=True,
    )
    responsable = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.PROTECT,
        db_column="id_usuario_responsable",
        related_name="abonos_registrados",
    )
    saldo_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_resultante = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "abono"
        verbose_name = "abono"
        verbose_name_plural = "abonos"
        ordering = ["-fecha", "-id_abono"]
        indexes = [
            models.Index(fields=["cuenta_cobro", "fecha"], name="idx_abono_cuenta"),
        ]

    def __str__(self):
        return f"Abono ${self.monto} a cuenta {self.cuenta_cobro_id}"


# ---------------------------------------------------------------------------
# Envíos y programación (ampliación de alcance del Módulo 6)
# ---------------------------------------------------------------------------

CORREO = "Correo"
WHATSAPP = "WhatsApp"
AMBOS = "Ambos"
OPCIONES_CANAL_ENVIO = [(CORREO, CORREO), (WHATSAPP, WHATSAPP), (AMBOS, "Correo y WhatsApp")]


class ConfiguracionCobro(models.Model):
    """
    Parámetros del proceso automático de cobro (una sola fila): generación
    mensual de cuentas de cobro y recordatorios automáticos de pago. Los
    ejecuta el comando `procesar_cobros` (cron) o el botón "Ejecutar ahora".
    """

    id_configuracion_cobro = models.AutoField(primary_key=True)
    cobro_automatico_activo = models.BooleanField(default=False)
    dia_generacion = models.PositiveSmallIntegerField(default=1)
    dias_plazo_pago = models.PositiveSmallIntegerField(default=10)
    canal_cobro = models.CharField(max_length=10, choices=OPCIONES_CANAL_ENVIO, default=CORREO)
    cuenta_bancaria = models.ForeignKey(
        CuentaBancaria,
        on_delete=models.SET_NULL,
        db_column="id_cuenta_bancaria",
        related_name="+",
        null=True,
        blank=True,
    )
    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.SET_NULL,
        db_column="id_metodo_pago",
        related_name="+",
        null=True,
        blank=True,
    )
    recordatorios_activos = models.BooleanField(default=False)
    dias_antes_vencimiento = models.PositiveSmallIntegerField(default=3)
    frecuencia_mora_dias = models.PositiveSmallIntegerField(default=7)
    canal_recordatorio = models.CharField(max_length=10, choices=OPCIONES_CANAL_ENVIO, default=CORREO)
    ultima_ejecucion = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "configuracion_cobro"
        verbose_name = "configuración de cobro"
        verbose_name_plural = "configuración de cobro"

    def __str__(self):
        return "Configuración del cobro automático"

    @classmethod
    def obtener(cls):
        """Devuelve la única fila de configuración, creándola con valores por defecto."""
        configuracion, _ = cls.objects.get_or_create(pk=1)
        return configuracion


class EnvioProgramado(models.Model):
    """
    Envío de una cuenta de cobro o de un recordatorio de pago programado para
    una fecha y hora. Los de correo se envían solos al llegar la hora; los de
    WhatsApp pasan a la bandeja de pendientes, porque el enlace `wa.me` exige
    que una persona pulse "Enviar".
    """

    CUENTA_COBRO = "Cuenta de cobro"
    RECORDATORIO = "Recordatorio"
    OPCIONES_TIPO = [(CUENTA_COBRO, CUENTA_COBRO), (RECORDATORIO, RECORDATORIO)]

    OPCIONES_CANAL = [(CORREO, CORREO), (WHATSAPP, WHATSAPP)]

    PROGRAMADO = "Programado"
    ENVIADO = "Enviado"
    FALLIDO = "Fallido"
    PENDIENTE_WHATSAPP = "Pendiente WhatsApp"
    CANCELADO = "Cancelado"
    OPCIONES_ESTADO = [
        (PROGRAMADO, PROGRAMADO),
        (ENVIADO, ENVIADO),
        (FALLIDO, FALLIDO),
        (PENDIENTE_WHATSAPP, PENDIENTE_WHATSAPP),
        (CANCELADO, CANCELADO),
    ]

    id_envio_programado = models.AutoField(primary_key=True)
    cuenta_cobro = models.ForeignKey(
        CuentaCobro,
        on_delete=models.CASCADE,
        db_column="id_cuenta_cobro",
        related_name="envios_programados",
    )
    tipo = models.CharField(max_length=20, choices=OPCIONES_TIPO, default=CUENTA_COBRO)
    canal = models.CharField(max_length=10, choices=OPCIONES_CANAL, default=CORREO)
    fecha_programada = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=OPCIONES_ESTADO, default=PROGRAMADO)
    usuario = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.SET_NULL,
        db_column="id_usuario",
        related_name="envios_programados",
        null=True,
        blank=True,
    )
    fecha_procesado = models.DateTimeField(null=True, blank=True)
    comunicacion = models.ForeignKey(
        "comunicaciones.Comunicacion",
        on_delete=models.SET_NULL,
        db_column="id_comunicacion",
        related_name="+",
        null=True,
        blank=True,
    )
    detalle_error = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "envio_programado"
        verbose_name = "envío programado"
        verbose_name_plural = "envíos programados"
        ordering = ["-fecha_programada"]
        indexes = [
            models.Index(fields=["estado", "fecha_programada"], name="idx_envio_estado_fecha"),
        ]

    def __str__(self):
        return f"{self.tipo} por {self.canal} - cuenta {self.cuenta_cobro_id} ({self.estado})"
