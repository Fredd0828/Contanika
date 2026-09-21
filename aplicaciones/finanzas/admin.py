"""Registro de los modelos del módulo 6 en el panel de administración."""

from django.contrib import admin

from .models import (
    Abono,
    ConceptoFacturable,
    CuentaBancaria,
    CuentaCobro,
    CuentaCobroDetalle,
    Honorario,
    MetodoPago,
)


class CuentaCobroDetalleInline(admin.TabularInline):
    model = CuentaCobroDetalle
    extra = 0


class AbonoInline(admin.TabularInline):
    model = Abono
    extra = 0
    readonly_fields = ["saldo_anterior", "saldo_resultante"]


@admin.register(Honorario)
class HonorarioAdmin(admin.ModelAdmin):
    list_display = ["cliente", "tipo", "monto"]
    list_filter = ["tipo"]
    search_fields = ["cliente__nombre_razon_social"]


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
