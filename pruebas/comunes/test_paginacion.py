"""Pruebas de la paginación común: ninguna tabla muestra más de 10 registros a la vez."""

import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.views.generic import ListView

from aplicaciones.comunes.paginacion import PaginacionMixin


class ListadoDePrueba(PaginacionMixin, ListView):
    """Listado mínimo sobre una lista en memoria, sin base de datos."""

    queryset = list(range(1, 36))
    template_name = "no_se_pinta.html"


def _contexto(parametros=""):
    solicitud = RequestFactory().get(f"/listado/{parametros}")
    respuesta = ListadoDePrueba.as_view()(solicitud)
    return respuesta.context_data


def test_muestra_diez_registros_por_defecto():
    contexto = _contexto()
    assert list(contexto["object_list"]) == list(range(1, 11))
    assert contexto["paginacion"]["por_pagina"] == 10
    assert contexto["paginator"].num_pages == 4


@pytest.mark.parametrize("valor", ["25", "50"])
def test_permite_elegir_25_o_50(valor):
    contexto = _contexto(f"?por_pagina={valor}")
    assert contexto["paginacion"]["por_pagina"] == int(valor)
    assert len(contexto["object_list"]) == min(int(valor), 35)


@pytest.mark.parametrize("valor", ["7", "1000", "abc", ""])
def test_un_tamano_no_permitido_vuelve_a_diez(valor):
    contexto = _contexto(f"?por_pagina={valor}")
    assert contexto["paginacion"]["por_pagina"] == 10
    assert len(contexto["object_list"]) == 10


def test_los_filtros_viajan_sin_pagina_ni_tamano():
    contexto = _contexto("?estado=Activo&page=2&por_pagina=25&etiqueta=a&etiqueta=b")
    paginacion = contexto["paginacion"]
    assert paginacion["consulta"] == "estado=Activo&etiqueta=a&etiqueta=b"
    assert paginacion["campos"] == [("estado", "Activo"), ("etiqueta", "a"), ("etiqueta", "b")]


def test_numeros_de_pagina_alrededor_de_la_actual():
    ListadoDePrueba.queryset = list(range(1, 101))
    try:
        assert _contexto("?page=1")["paginacion"]["paginas"] == [1, 2, 3]
        assert _contexto("?page=5")["paginacion"]["paginas"] == [3, 4, 5, 6, 7]
        assert _contexto("?page=10")["paginacion"]["paginas"] == [8, 9, 10]
    finally:
        ListadoDePrueba.queryset = list(range(1, 36))


def test_con_diez_registros_o_menos_no_hay_pie():
    ListadoDePrueba.queryset = list(range(1, 11))
    try:
        assert _contexto()["paginacion"]["visible"] is False
    finally:
        ListadoDePrueba.queryset = list(range(1, 36))


def test_el_pie_no_desaparece_al_elegir_50():
    """Con 35 registros y 50 por página todo cabe, pero el selector sigue a la vista."""
    contexto = _contexto("?por_pagina=50")
    assert contexto["paginator"].num_pages == 1
    assert contexto["paginacion"]["visible"] is True


def test_plantilla_del_pie_conserva_filtros_y_tamano():
    contexto = _contexto("?estado=Activo&page=2")
    html = render_to_string("comunes/_paginacion.html", contexto)
    assert 'name="estado" value="Activo"' in html
    assert "?page=3&por_pagina=10&estado=Activo" in html
    assert "?page=1&por_pagina=10&estado=Activo" in html
    assert "Página 2 de 4 · 35 registro(s)" in html
    assert 'class="pg-pie panel mt-3"' in html


def test_plantilla_del_pie_dentro_del_panel():
    contexto = _contexto()
    contexto["dentro_de_panel"] = True
    html = render_to_string("comunes/_paginacion.html", contexto)
    assert 'class="pg-pie"' in html


def test_plantilla_del_pie_escapa_los_filtros():
    contexto = _contexto('?busqueda="><script>alert(1)</script>')
    html = render_to_string("comunes/_paginacion.html", contexto)
    assert "<script>alert(1)</script>" not in html
