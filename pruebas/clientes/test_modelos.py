"""Pruebas de los modelos del módulo 1: clientes y credenciales."""

from datetime import timedelta

import pytest
from django.utils import timezone

from aplicaciones.clientes.models import (
    Cliente,
    ClienteMunicipio,
    ClienteServicio,
    Credencial,
    TipoServicio,
)

pytestmark = pytest.mark.django_db


def test_inactivar_cliente_conserva_el_registro(cliente):
    """Inactivar un cliente no lo elimina: conserva su historial."""
    cliente.inactivar()
    cliente.refresh_from_db()
    assert cliente.estado == Cliente.INACTIVO
    assert Cliente.objects.filter(pk=cliente.pk).exists()


def test_municipios_adicionales_multi_ica(cliente):
    """El cliente puede tener varios municipios adicionales (multi-ICA)."""
    ClienteMunicipio.objects.create(cliente=cliente, municipio="Medellín")
    ClienteMunicipio.objects.create(cliente=cliente, municipio="Cali")
    assert cliente.municipios_adicionales.count() == 2


def test_servicios_del_cliente(cliente):
    """La relación N:M entre cliente y tipos de servicio funciona."""
    renta = TipoServicio.objects.create(nombre_servicio="Declaración de renta")
    iva = TipoServicio.objects.create(nombre_servicio="Declaración de IVA")
    ClienteServicio.objects.create(cliente=cliente, tipo_servicio=renta)
    ClienteServicio.objects.create(cliente=cliente, tipo_servicio=iva)
    assert cliente.servicios.count() == 2


def test_credencial_requiere_actualizacion_despues_de_90_dias(cliente, usuario_administrador):
    """Una credencial con más de 90 días sin actualizar genera aviso visual."""
    credencial = Credencial.objects.create(
        cliente=cliente,
        concepto="DIAN",
        usuario_acceso="900123456",
        clave_cifrada="clave-cifrada-de-prueba",
    )
    Credencial.objects.filter(pk=credencial.pk).update(
        fecha_ultima_actualizacion=timezone.now() - timedelta(days=91)
    )
    credencial.refresh_from_db()
    assert credencial.dias_sin_actualizacion >= 91
    assert credencial.requiere_actualizacion is True


def test_credencial_reciente_no_requiere_actualizacion(cliente, usuario_administrador):
    """Una credencial recién actualizada no genera aviso."""
    credencial = Credencial.objects.create(
        cliente=cliente,
        concepto="Secretaría de Hacienda",
        usuario_acceso="usuario-hacienda",
        clave_cifrada="clave-cifrada-de-prueba",
    )
    assert credencial.requiere_actualizacion is False
