"""
Paginación común de los listados.

Todos los listados de la plataforma muestran 10 registros por página y dejan
elegir 25 o 50, igual que el de clientes. La vista hereda de
`PaginacionMixin` (antes de `ListView`) y la plantilla incluye
`comunes/_paginacion.html`, que pinta el selector, los números de página y el
total. Las tablas que no salen de un `ListView` (reportes, cartera, fichas)
se reparten de a 10 en el navegador con el guion de `base.html`.
"""

VENTANA_PAGINAS = 2


class PaginacionMixin:
    """Da a un `ListView` la paginación de 10 registros con selector."""

    OPCIONES_POR_PAGINA = (10, 25, 50)
    POR_PAGINA_DEFAULT = 10

    def get_paginate_by(self, queryset):
        """Permite al usuario elegir cuántos registros ver por página."""
        try:
            valor = int(self.request.GET.get("por_pagina", self.POR_PAGINA_DEFAULT))
        except ValueError:
            return self.POR_PAGINA_DEFAULT
        return valor if valor in self.OPCIONES_POR_PAGINA else self.POR_PAGINA_DEFAULT

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        # Los filtros vigentes viajan en cada enlace; la página y el tamaño los
        # pone la plantilla.
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        parametros.pop("por_pagina", None)
        paginador = contexto.get("paginator")
        pagina = contexto.get("page_obj")
        paginas = []
        if paginador is not None and pagina is not None:
            desde = max(1, pagina.number - VENTANA_PAGINAS)
            hasta = min(paginador.num_pages, pagina.number + VENTANA_PAGINAS)
            paginas = list(range(desde, hasta + 1))
        contexto["paginacion"] = {
            "por_pagina": self.get_paginate_by(None),
            "opciones": self.OPCIONES_POR_PAGINA,
            "consulta": parametros.urlencode(),
            "campos": [(clave, valor) for clave in parametros for valor in parametros.getlist(clave)],
            "paginas": paginas,
            # Con 10 registros o menos no hay nada que repartir. Se compara con
            # la opción más pequeña para que el selector no desaparezca cuando
            # el usuario elige ver 50 y todos caben en una página.
            "visible": paginador is not None and paginador.count > min(self.OPCIONES_POR_PAGINA),
        }
        return contexto
