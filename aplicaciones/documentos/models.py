"""
Modelos del módulo 4: expedición de documentos y certificados.

Define las plantillas con sus campos variables (simples o repetibles), los
documentos generados para cada cliente y los valores capturados, que luego
se imprimen en el PDF con ReportLab.
"""

from django.db import models


class Plantilla(models.Model):
    """
    Plantilla de documento o certificado.

    Incluye las seis plantillas base del sistema y las que cree el
    Administrador; el texto predeterminado puede contener marcadores que se
    reemplazan con los valores de cada campo variable.
    """

    id_plantilla = models.AutoField(primary_key=True)
    nombre_plantilla = models.CharField(max_length=100)
    texto_predeterminado = models.TextField(blank=True)
    tipo_documento = models.CharField(max_length=60)

    class Meta:
        db_table = "plantilla"
        verbose_name = "plantilla"
        verbose_name_plural = "plantillas"
        ordering = ["nombre_plantilla"]

    def __str__(self):
        return self.nombre_plantilla


class CampoPlantilla(models.Model):
    """Campo variable propio de una plantilla, simple o repetible (por ejemplo, accionistas)."""

    SIMPLE = "Simple"
    REPETIBLE = "Repetible"
    OPCIONES_TIPO_CAMPO = [(SIMPLE, SIMPLE), (REPETIBLE, REPETIBLE)]

    id_campo = models.AutoField(primary_key=True)
    plantilla = models.ForeignKey(
        Plantilla,
        on_delete=models.CASCADE,
        db_column="id_plantilla",
        related_name="campos",
    )
    nombre_campo = models.CharField(max_length=80)
    tipo_campo = models.CharField(max_length=20, choices=OPCIONES_TIPO_CAMPO, default=SIMPLE)
    es_repetible = models.BooleanField(default=False)

    class Meta:
        db_table = "campo_plantilla"
        verbose_name = "campo de plantilla"
        verbose_name_plural = "campos de plantillas"
        ordering = ["plantilla", "id_campo"]
        constraints = [
            models.UniqueConstraint(fields=["plantilla", "nombre_campo"], name="unico_campo_plantilla"),
        ]

    def __str__(self):
        return f"{self.nombre_campo} ({self.tipo_campo})"


class Documento(models.Model):
    """Documento o certificado generado para un cliente, almacenado como PDF."""

    id_documento = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        db_column="id_cliente",
        related_name="documentos",
    )
    plantilla = models.ForeignKey(
        Plantilla,
        on_delete=models.PROTECT,
        db_column="id_plantilla",
        related_name="documentos",
    )
    usuario_generador = models.ForeignKey(
        "seguridad.Usuario",
        on_delete=models.PROTECT,
        db_column="id_usuario_generador",
        related_name="documentos_generados",
    )
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    periodo = models.CharField(max_length=60, blank=True)
    descripcion = models.TextField(blank=True)
    archivo = models.FileField(upload_to="documentos/%Y/%m/", max_length=255, blank=True)

    class Meta:
        db_table = "documento"
        verbose_name = "documento"
        verbose_name_plural = "documentos"
        ordering = ["-fecha_generacion"]
        indexes = [
            models.Index(fields=["cliente", "plantilla"], name="idx_documento_cliente"),
        ]

    def __str__(self):
        return f"{self.plantilla.nombre_plantilla} - {self.cliente.nombre_razon_social}"


class DocumentoValor(models.Model):
    """Valor de un campo simple para un documento generado."""

    id_valor = models.AutoField(primary_key=True)
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        db_column="id_documento",
        related_name="valores",
    )
    campo = models.ForeignKey(
        CampoPlantilla,
        on_delete=models.PROTECT,
        db_column="id_campo",
        related_name="valores",
    )
    valor = models.TextField(blank=True)

    class Meta:
        db_table = "documento_valor"
        verbose_name = "valor de documento"
        verbose_name_plural = "valores de documentos"
        constraints = [
            models.UniqueConstraint(fields=["documento", "campo"], name="unico_documento_campo"),
        ]

    def __str__(self):
        return f"{self.campo.nombre_campo}: {self.valor}"


class DocumentoDetalle(models.Model):
    """
    Fila de un campo repetible para un documento generado.

    Por ejemplo, cada accionista del certificado de composición accionaria:
    `fila` indica la posición dentro de la lista repetible.
    """

    id_detalle = models.AutoField(primary_key=True)
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        db_column="id_documento",
        related_name="detalles",
    )
    campo = models.ForeignKey(
        CampoPlantilla,
        on_delete=models.PROTECT,
        db_column="id_campo",
        related_name="detalles",
    )
    fila = models.PositiveIntegerField(default=1)
    valor = models.TextField(blank=True)

    class Meta:
        db_table = "documento_detalle"
        verbose_name = "detalle de documento"
        verbose_name_plural = "detalles de documentos"
        ordering = ["documento", "campo", "fila"]

    def __str__(self):
        return f"{self.campo.nombre_campo} fila {self.fila}: {self.valor}"
