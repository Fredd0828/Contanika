"""Registro de los modelos del módulo 6 en el panel de administración."""

from django.contrib import admin

from .models import (
    Abono,
    ConceptoFacturable,
    ConfiguracionCobro,
    CuentaBancaria,
    CuentaCobro,
    CuentaCobroDetalle,
    EnvioProgramado,
    Honorario,
    HonorarioServicio,
    MetodoPago,
)


@admin.register(ConfiguracionCobro)
class ConfiguracionCobroAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "cobro_automatico_activo",
        "dia_generacion",
        "recordatorios_activos",
        "ultima_ejecucion",
    ]


@admin.register(EnvioProgramado)
class EnvioProgramadoAdmin(admin.ModelAdmin):
    list_display = ["cuenta_cobro", "tipo", "canal", "fecha_programada", "estado", "usuario"]
    list_filter = ["estado", "tipo", "canal"]
    search_fields = ["cuenta_cobro__cliente__nombre_razon_social"]


class CuentaCobroDetalleInline(admin.TabularInline):
    model = CuentaCobroDetalle
    extra = 0


class HonorarioServicioInline(admin.TabularInline):
    model = HonorarioServicio
    extra = 0


class AbonoInline(admin.TabularInline):
    """Solo consulta: los abonos se registran desde la aplicación y el disparador los hace inmutables."""

    model = Abono
    extra = 0
    can_delete = False
    readonly_fields = ["fecha", "monto", "metodo_pago", "responsable", "saldo_anterior", "saldo_resultante"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Honorario)
class HonorarioAdmin(admin.ModelAdmin):
    list_display = ["cliente", "tipo", "monto", "usuario_actualizacion", "fecha_actualizacion"]
    list_filter = ["tipo"]
    search_fields = ["cliente__nombre_razon_social"]
    inlines = [HonorarioServicioInline]


@admin.register(ConceptoFacturable)
class ConceptoFacturableAdmin(admin.ModelAdmin):
    list_display = ["nombre_concepto", "valor_sugerido"]
    search_fields = ["nombre_concepto"]


@admin.register(CuentaBancaria)
class CuentaBancariaAdmin(admin.ModelAdmin):
    list_display = ["banco", "tipo_cuenta", "numero_cuenta", "titular"]
    search_fields = ["banco", "numero_cuenta", "titular"]


@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ["nombre_metodo"]
    search_fields = ["nombre_metodo"]


@admin.register(CuentaCobro)
class CuentaCobroAdmin(admin.ModelAdmin):
    list_display = [
        "id_cuenta_cobro",
        "cliente",
        "periodo_facturado",
        "valor_total",
        "estado_envio",
        "estado_pago",
        "fecha_vencimiento_pago",
    ]
    list_filter = ["estado_envio", "estado_pago", "periodo_facturado"]
    search_fields = ["cliente__nombre_razon_social"]
    inlines = [CuentaCobroDetalleInline, AbonoInline]
