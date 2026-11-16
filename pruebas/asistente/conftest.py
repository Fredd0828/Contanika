"""Datos de apoyo para las pruebas del asistente de consultas."""

from datetime import date
from decimal import Decimal

import pytest

from aplicaciones.calendario.models import Vencimiento
from aplicaciones.finanzas.models import Abono, CuentaCobro
from aplicaciones.hallazgos.models import Hallazgo
from aplicaciones.seguridad.models import Modulo, PermisoRolModulo
from aplicaciones.tareas.models import Tarea

# Lunes: la semana del asistente va del 16 al 22 de noviembre.
HOY = date(2026, 11, 16)


def crear_vencimiento(cliente, fecha, estado=Vencimiento.PENDIENTE, tipo="IVA bimestral", responsable=None):
    return Vencimiento.objects.create(
        cliente=cliente,
        tipo_obligacion=tipo,
        fecha_vencimiento=fecha,
        estado_presentacion=estado,
        responsable=responsable,
    )


def crear_tarea(cliente, titulo, **campos):
    return Tarea.objects.create(cliente=cliente, titulo=titulo, **campos)


def crear_hallazgo(cliente, **campos):
    datos = {
        "tipo_hallazgo": "Conciliación bancaria",
        "fecha_inicio_periodo": date(2026, 10, 1),
        "fecha_fin_periodo": date(2026, 10, 31),
        "descripcion": "Diferencia en la conciliación.",
    }
    datos.update(campos)
    return Hallazgo.objects.create(cliente=cliente, **datos)


def crear_cuenta(cliente, valor, vence):
    return CuentaCobro.objects.create(
        cliente=cliente, valor_total=Decimal(valor), fecha_vencimiento_pago=vence
    )


def abonar(cuenta, monto, usuario):
    return Abono.objects.create(
        cuenta_cobro=cuenta,
        fecha=HOY,
        monto=Decimal(monto),
        responsable=usuario,
        saldo_anterior=Decimal("0"),
        saldo_resultante=Decimal("0"),
    )


def inhabilitar(rol, codigo_modulo):
    """Apaga un módulo o sección para un rol, como lo haría el Administrador."""
    modulo, _ = Modulo.objects.get_or_create(
        codigo_modulo=codigo_modulo, defaults={"nombre_modulo": codigo_modulo}
    )
    PermisoRolModulo.objects.update_or_create(rol=rol, modulo=modulo, defaults={"habilitado": False})


@pytest.fixture
def hoy():
    return HOY
