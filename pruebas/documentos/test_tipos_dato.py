"""
Campos de plantilla que solo aceptan números (23-nov-2026): valores en pesos,
identificaciones y porcentajes, al generar un documento.
"""

import pytest
from django.core.management import call_command

from aplicaciones.documentos.formularios import (
    CampoPesos,
    CampoPorcentaje,
    construir_formset_filas_repetibles,
    construir_formulario_campos_simples,
)
from aplicaciones.documentos.models import CampoPlantilla, Plantilla


@pytest.mark.parametrize(
    ("escrito", "guardado"),
    [
        ("1250000", "1.250.000"),
        ("1.250.000", "1.250.000"),
        ("$ 1.250.000", "1.250.000"),
        ("1250000,5", "1.250.000,50"),
        ("1.250.000,00", "1.250.000"),
        ("0", "0"),
        ("999", "999"),
    ],
)
def test_pesos_se_guarda_con_puntos_de_miles(escrito, guardado):
    assert CampoPesos().clean(escrito) == guardado


@pytest.mark.parametrize(
    "escrito", ["ffsdfsdfsdfsfs", "12a00", "1,250,000", "12.50", "1.2345", "1250000,555", "-500"]
)
def test_pesos_rechaza_lo_que_no_es_un_valor(escrito):
    with pytest.raises(Exception, match="solo el valor en números"):
        CampoPesos().clean(escrito)


@pytest.mark.parametrize(
    ("escrito", "guardado"), [("50", "50"), ("33,5", "33,5"), ("33.33", "33,33"), ("100", "100")]
)
def test_porcentaje_valido(escrito, guardado):
    assert CampoPorcentaje().clean(escrito) == guardado


@pytest.mark.parametrize("escrito", ["101", "abc", "5o", "1000", "12,345"])
def test_porcentaje_invalido(escrito):
    with pytest.raises(Exception, match="porcentaje entre 0 y 100"):
        CampoPorcentaje().clean(escrito)


@pytest.mark.parametrize(
    ("nombre", "tipo"),
    [
        ("Valor del patrimonio", CampoPlantilla.PESOS),
        ("Total de activos", CampoPlantilla.PESOS),
        ("Total de pasivos", CampoPlantilla.PESOS),
        ("Ingresos brutos", CampoPlantilla.PESOS),
        ("Monto de la retención", CampoPlantilla.PESOS),
        ("Consignaciones, compras y consumos del período", CampoPlantilla.PESOS),
        ("Identificación del asalariado", CampoPlantilla.NUMERO),
        ("Porcentaje de participación", CampoPlantilla.PORCENTAJE),
        ("Concepto", CampoPlantilla.TEXTO),
        ("Base de la certificación", CampoPlantilla.TEXTO),
        ("Nombre del accionista", CampoPlantilla.TEXTO),
    ],
)
def test_tipo_dato_sugerido_por_el_nombre(nombre, tipo):
    assert CampoPlantilla.tipo_dato_sugerido(nombre) == tipo


@pytest.mark.django_db
def test_formulario_de_campos_valida_segun_el_tipo():
    plantilla = Plantilla.objects.create(nombre_plantilla="Patrimonio", tipo_documento="Certificado")
    pesos = CampoPlantilla.objects.create(
        plantilla=plantilla, nombre_campo="Valor del patrimonio", tipo_dato=CampoPlantilla.PESOS
    )
    numero = CampoPlantilla.objects.create(
        plantilla=plantilla, nombre_campo="Identificación", tipo_dato=CampoPlantilla.NUMERO
    )
    texto = CampoPlantilla.objects.create(
        plantilla=plantilla, nombre_campo="Base", tipo_dato=CampoPlantilla.TEXTO
    )

    vacio = construir_formulario_campos_simples(plantilla)
    assert vacio.fields[f"campo_{pesos.pk}"].widget.attrs["data-solo-numeros"] == "pesos"
    assert vacio.fields[f"campo_{numero.pk}"].widget.attrs["data-solo-numeros"] == "digitos"
    assert "data-solo-numeros" not in vacio.fields[f"campo_{texto.pk}"].widget.attrs

    malo = construir_formulario_campos_simples(
        plantilla,
        {f"campo_{pesos.pk}": "fdfdfdfs", f"campo_{numero.pk}": "12-3", f"campo_{texto.pk}": "Balance"},
    )
    assert not malo.is_valid()
    assert set(malo.errors) == {f"campo_{pesos.pk}", f"campo_{numero.pk}"}

    bueno = construir_formulario_campos_simples(
        plantilla,
        {f"campo_{pesos.pk}": "85000000", f"campo_{numero.pk}": "1032456789", f"campo_{texto.pk}": "Balance"},
    )
    assert bueno.is_valid()
    assert bueno.cleaned_data[f"campo_{pesos.pk}"] == "85.000.000"


@pytest.mark.django_db
def test_filas_repetibles_validan_el_porcentaje():
    plantilla = Plantilla.objects.create(nombre_plantilla="Accionistas", tipo_documento="Certificado")
    porcentaje = CampoPlantilla.objects.create(
        plantilla=plantilla,
        nombre_campo="Porcentaje de participación",
        tipo_campo=CampoPlantilla.REPETIBLE,
        es_repetible=True,
        tipo_dato=CampoPlantilla.PORCENTAJE,
    )
    datos = {
        "filas-TOTAL_FORMS": "1",
        "filas-INITIAL_FORMS": "0",
        f"filas-0-campo_{porcentaje.pk}": "cincuenta",
    }
    formset = construir_formset_filas_repetibles(plantilla, datos)
    assert not formset.is_valid()


@pytest.mark.django_db
def test_las_plantillas_base_quedan_con_su_tipo_de_dato():
    call_command("cargar_datos_iniciales", verbosity=0)
    patrimonio = CampoPlantilla.objects.get(nombre_campo="Valor del patrimonio")
    assert patrimonio.tipo_dato == CampoPlantilla.PESOS
    assert (
        CampoPlantilla.objects.get(nombre_campo="Identificación del asalariado").tipo_dato
        == CampoPlantilla.NUMERO
    )
    assert (
        CampoPlantilla.objects.get(nombre_campo="Porcentaje de participación").tipo_dato
        == CampoPlantilla.PORCENTAJE
    )
    assert CampoPlantilla.objects.filter(nombre_campo="Concepto", tipo_dato=CampoPlantilla.TEXTO).exists()
