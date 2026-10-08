"""Fixtures del módulo 6: honorarios, catálogos y cuentas de cobro."""

from datetime import date
from decimal import Decimal

import pytest

from aplicaciones.clientes.models import ClienteServicio, TipoServicio
from aplicaciones.finanzas import servicios
from aplicaciones.finanzas.models import ConceptoFacturable, CuentaBancaria, MetodoPago
from aplicaciones.seguridad.models import ConfiguracionDespacho


@pytest.fixture(autouse=True)
def media_root_temporal(settings, tmp_path):
    """Redirige los PDF generados en las pruebas a un directorio temporal."""
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def despacho(db):
    return ConfiguracionDespacho.objects.create(
        pk=1, nombre_despacho="Befrec Y Asociados SAS", nit_despacho="900111222-3", ciudad="Bogotá D.C."
    )


@pytest.fixture
def servicio_contabilidad(db):
    return TipoServicio.objects.create(nombre_servicio="Contabilidad mensual")


@pytest.fixture
def servicio_nomina(db):
    return TipoServicio.objects.create(nombre_servicio="Nómina")


@pytest.fixture
def cliente_con_servicios(cliente, servicio_contabilidad, servicio_nomina):
    ClienteServicio.objects.create(cliente=cliente, tipo_servicio=servicio_contabilidad)
    ClienteServicio.objects.create(cliente=cliente, tipo_servicio=servicio_nomina)
    return cliente


@pytest.fixture
def cuenta_bancaria(db):
    return CuentaBancaria.objects.create(
        banco="Bancolombia",
        tipo_cuenta="Ahorros",
        numero_cuenta="123-456789-01",
        titular="Befrec Y Asociados SAS",
    )


@pytest.fixture
def metodo_transferencia(db):
    return MetodoPago.objects.create(nombre_metodo="Transferencia")


@pytest.fixture
def concepto_revisoria(db):
    return ConceptoFacturable.objects.create(
        nombre_concepto="Revisoría fiscal", valor_sugerido=Decimal("300000")
    )


def _generar(cliente, valor_total=Decimal("1000000"), lineas=None, **extra):
    datos = {
        "cliente": cliente,
        "periodo_facturado": "Mensual",
        "fecha_inicio_periodo": date(2026, 9, 1),
        "fecha_fin_periodo": date(2026, 9, 30),
        "valor_total": valor_total,
        "cuenta_bancaria": None,
        "metodo_pago": None,
        "fecha_vencimiento_pago": date(2026, 10, 10),
        "lineas": lineas or [{"descripcion_linea": "Contabilidad mensual", "valor_linea": None}],
    }
    datos.update(extra)
    return servicios.generar_cuenta_cobro(**datos)


@pytest.fixture
def generar_cuenta(despacho):
    """Fábrica de cuentas de cobro generadas por el servicio real (con PDF)."""
    return _generar


@pytest.fixture
def cuenta_cliente(generar_cuenta, cliente):
    return generar_cuenta(cliente)


@pytest.fixture
def cuenta_cliente_junior(generar_cuenta, cliente_junior):
    return generar_cuenta(cliente_junior, valor_total=Decimal("500000"))
