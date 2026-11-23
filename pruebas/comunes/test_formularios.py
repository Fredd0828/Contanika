"""
Campos que solo aceptan números (pedido del usuario, 23-nov-2026).

El mixin común de formularios los reconoce por su nombre: les pone el teclado
numérico y el filtro del navegador, y el servidor rechaza cualquier otro
carácter aunque alguien se salte el filtro.
"""

import pytest
from django import forms

from aplicaciones.comunes.formularios import FormularioBase


class _Formulario(FormularioBase):
    telefono = forms.CharField(required=False)
    identificacion = forms.CharField(required=False)
    numero_cuenta = forms.CharField(required=False)
    nit_cedula = forms.CharField(required=False)
    nit_despacho = forms.CharField(required=False)
    nombre = forms.CharField(required=False)


@pytest.mark.parametrize("campo", ["telefono", "identificacion", "numero_cuenta", "nit_cedula"])
def test_campos_de_solo_digitos_llevan_teclado_numerico_y_filtro(campo):
    atributos = _Formulario().fields[campo].widget.attrs
    assert atributos["inputmode"] == "numeric"
    assert atributos["data-solo-numeros"] == "digitos"


@pytest.mark.parametrize("campo", ["telefono", "identificacion", "numero_cuenta", "nit_cedula"])
@pytest.mark.parametrize("valor", ["31A5", "316 044", "1.032.456", "+573160444428", "12-3"])
def test_campos_de_solo_digitos_rechazan_otros_caracteres(campo, valor):
    formulario = _Formulario({campo: valor})
    assert not formulario.is_valid()
    assert "Escriba solo números" in formulario.errors[campo][0]


@pytest.mark.parametrize("campo", ["telefono", "identificacion", "numero_cuenta", "nit_cedula"])
def test_campos_de_solo_digitos_aceptan_numeros_y_vacio(campo):
    assert _Formulario({campo: "3160444428"}).is_valid()
    assert _Formulario({campo: ""}).is_valid()


@pytest.mark.parametrize("valor", ["900123456", "900123456-7", ""])
def test_nit_del_despacho_acepta_digito_de_verificacion(valor):
    assert _Formulario({"nit_despacho": valor}).is_valid()


@pytest.mark.parametrize("valor", ["900A23456", "900.123.456-7", "900123456-78", "-7"])
def test_nit_del_despacho_rechaza_otros_caracteres(valor):
    formulario = _Formulario({"nit_despacho": valor})
    assert not formulario.is_valid()
    assert _Formulario().fields["nit_despacho"].widget.attrs["data-solo-numeros"] == "nit"


def test_un_campo_de_texto_comun_no_se_toca():
    formulario = _Formulario({"nombre": "Paula 2026"})
    assert formulario.is_valid()
    assert "data-solo-numeros" not in formulario.fields["nombre"].widget.attrs
