"""
Modelos del módulo 7: comunicaciones integradas.

Registra de forma automática las comunicaciones enviadas desde otros módulos
(calendario, documentos, honorarios) y las manuales (llamadas o reuniones),
con su canal, estado de envío y usuario responsable.
"""

from django.db import models


class Comunicacion(models.Model):
    """Comunicación automática o manual registrada con un cliente."""

    CORREO = "Correo"
    WHATSAPP = "WhatsApp"
    LLAMADA = "Llamada"
    REUNION = "Reunión presencial"
    OPCIONES_CANAL = [
        (CORREO, CORREO),
        (WHATSAPP, WHATSAPP),
        (LLAMADA, LLAMADA),
        (REUNION, REUNION),
    ]

    AUTOMATICA = "Automática"
    MANUAL = "Manual"
    OPCIONES_TIPO = [(AUTOMATICA, AUTOMATICA), (MANUAL, MANUAL)]

    EXITO = "Éxito"
    FALLO = "Fallo"
    REINTENTANDO = "Reintentando"
    OPCIONES_ESTADO_ENVIO = [(EXITO, EXITO), (FALLO, FALLO), (REINTENTANDO, REINTENTANDO)]

    id_comunicacion = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        db_column="id_cliente",
        related_name="comunicaciones",
    )
    canal = models.CharField(max_length=20, choices=OPCIONES_CANAL)
    tipo = models.CharField(max_length=15, choices=OPCIONES_TIPO, default=MANUAL)
    contenido_resumen = models.TextField(blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.PROTECT,
        db_column="id_usuario",
        related_name="comunicaciones_registradas",
        null=True,
        blank=True,
    )
    estado_envio = models.CharField(max_length=20, choices=OPCIONES_ESTADO_ENVIO, default=EXITO)
    numero_reintentos = models.PositiveIntegerField(default=0)
    modulo_origen = models.CharField(max_length=30, blank=True)

    class Meta:
        db_table = "comunicacion"
        verbose_name = "comunicación"
        verbose_name_plural = "comunicaciones"
        ordering = ["-fecha_hora"]
        indexes = [
            models.Index(fields=["cliente", "-fecha_hora"], name="idx_comunicacion_cliente"),
        ]

    def __str__(self):
        return f"{self.canal} ({self.tipo}) - {self.cliente.nombre_razon_social}"
