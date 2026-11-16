"""Pruebas del comando que regenera el PDF guardado de las cuentas de cobro."""

from io import StringIO

import pytest
from django.core.management import call_command

from aplicaciones.finanzas import servicios

pytestmark = pytest.mark.django_db


def _correr(*argumentos):
    salida = StringIO()
    call_command("regenerar_pdf_cuentas", *argumentos, stdout=salida)
    return salida.getvalue()


def _contenido(cuenta):
    cuenta.refresh_from_db()
    with cuenta.archivo.open("rb") as archivo:
        return archivo.read()


def test_sin_aplicar_no_cambia_nada(cuenta_cliente):
    antes = _contenido(cuenta_cliente)
    salida = _correr()
    assert "Hay 1 cuenta(s)" in salida
    assert _contenido(cuenta_cliente) == antes


def test_con_aplicar_rehace_el_pdf_sin_tocar_los_datos(cuenta_cliente, monkeypatch):
    valor, estado = cuenta_cliente.valor_total, cuenta_cliente.estado_pago
    monkeypatch.setattr(servicios, "construir_pdf_cuenta_cobro", lambda cuenta: b"%PDF-nuevo")
    salida = _correr("--aplicar")
    assert "PDF regenerados: 1 de 1" in salida
    assert _contenido(cuenta_cliente) == b"%PDF-nuevo"
    assert (cuenta_cliente.valor_total, cuenta_cliente.estado_pago) == (valor, estado)


def test_una_cuenta_que_falla_no_detiene_las_demas(generar_cuenta, cliente, cliente_junior, monkeypatch):
    primera = generar_cuenta(cliente)
    generar_cuenta(cliente_junior)

    def construir(cuenta):
        if cuenta.pk == primera.pk:
            raise ValueError("dato dañado")
        return b"%PDF-nuevo"

    monkeypatch.setattr(servicios, "construir_pdf_cuenta_cobro", construir)
    salida = _correr("--aplicar")
    assert "PDF regenerados: 1 de 2" in salida
    assert f"Cuenta {primera.pk}: no se pudo regenerar (dato dañado)" in salida
