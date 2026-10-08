"""
Vistas del módulo 10: reportes y análisis.

Permisos (spec y HU028):
- Los tres roles acceden al módulo; cada reporte se muestra solo a los roles
  que el Administrador habilitó (un reporte oculto tampoco se abre por URL).
- Senior y Junior ven en los reportes solo sus clientes asignados; el de
  ingresos es siempre el consolidado del despacho.
- Visibilidad por rol e historial de descargas: solo el Administrador.
"""

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import ListView, TemplateView, View

from aplicaciones.comunes.formularios import FormularioBase
from aplicaciones.seguridad.models import Modulo, Rol
from aplicaciones.seguridad.permisos import ModuloHabilitadoMixin, RolRequeridoMixin

from . import exportadores, selectores, servicios
from .definiciones import POR_SLUG
from .models import DescargaReporte, Reporte
from .resultados import FECHA, NUMERO, PESOS, PORCENTAJE

Usuario = get_user_model()

# En pantalla se muestran hasta estas filas por sección; la descarga trae todas.
FILAS_EN_PANTALLA = 200

TIPOS_CONTENIDO = {
    DescargaReporte.EXCEL: ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"),
    DescargaReporte.PDF: ("application/pdf", "pdf"),
}


class InicioReportesView(ModuloHabilitadoMixin, TemplateView):
    """Tarjetas de los reportes visibles para el rol del usuario."""

    codigo_modulo = Modulo.MOD10_REPORTES
    template_name = "reportes/inicio.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["reportes"] = selectores.reportes_visibles(self.request.user)
        return contexto


class ReporteView(ModuloHabilitadoMixin, View):
    """Filtros, vista previa y descarga en Excel o PDF de un reporte."""

    codigo_modulo = Modulo.MOD10_REPORTES

    def _definicion(self, request, slug):
        definicion = POR_SLUG.get(slug)
        if definicion is None:
            raise Http404("El reporte no existe.")
        if not selectores.puede_ver(request.user, definicion):
            raise PermissionDenied("El reporte no está habilitado para su rol.")
        return definicion

    def get(self, request, slug):
        definicion = self._definicion(request, slug)
        formulario = definicion.formulario(request.GET or None, usuario=request.user)
        filtros = formulario.cleaned_data if formulario.is_bound and formulario.is_valid() else {}
        if formulario.is_bound and not formulario.is_valid():
            resultado = None
        else:
            resultado = definicion.generar(request.user, filtros)

        formato = request.GET.get("formato")
        if formato in TIPOS_CONTENIDO and resultado is not None:
            return self._descargar(request, definicion, resultado, formulario, formato)

        parametros = request.GET.copy()
        parametros.pop("formato", None)
        contexto = {
            "definicion": definicion,
            "formulario": formulario,
            "resultado": resultado,
            "secciones": _secciones_para_pantalla(resultado) if resultado else [],
            "grafico": _datos_grafico(resultado),
            "querystring": parametros.urlencode(),
            "filas_en_pantalla": FILAS_EN_PANTALLA,
        }
        return render(request, "reportes/reporte.html", contexto)

    def _descargar(self, request, definicion, resultado, formulario, formato):
        filtros_texto = formulario.resumen_filtros() if formulario.is_bound else ""
        exportar = (
            exportadores.exportar_excel if formato == DescargaReporte.EXCEL else exportadores.exportar_pdf
        )
        contenido = exportar(definicion, resultado, request.user, filtros_texto)
        servicios.registrar_descarga(definicion.nombre, request.user, formato, filtros_texto)
        tipo, extension = TIPOS_CONTENIDO[formato]
        nombre = f"reporte_{slugify(definicion.slug)}_{timezone.localdate():%Y%m%d}.{extension}"
        respuesta = HttpResponse(contenido, content_type=tipo)
        respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
        return respuesta


def _secciones_para_pantalla(resultado):
    """Celdas ya formateadas (pesos, fechas, porcentajes) para la plantilla."""
    secciones = []
    for seccion in resultado.secciones:
        filas = []
        for indice, fila in enumerate(seccion.filas[:FILAS_EN_PANTALLA]):
            celdas = [
                {
                    "texto": exportadores.formatear(valor, columna.tipo),
                    "derecha": columna.tipo in (PESOS, NUMERO, PORCENTAJE),
                    "fecha": columna.tipo == FECHA,
                }
                for valor, columna in zip(fila, seccion.columnas, strict=True)
            ]
            filas.append({"celdas": celdas, "resaltada": indice in seccion.resaltadas})
        secciones.append(
            {
                "titulo": seccion.titulo,
                "columnas": seccion.columnas,
                "filas": filas,
                "total": len(seccion.filas),
                "recortada": len(seccion.filas) > FILAS_EN_PANTALLA,
                "nota_resaltado": seccion.nota_resaltado if seccion.resaltadas else "",
            }
        )
    return secciones


def _datos_grafico(resultado):
    """Datos del gráfico para la plantilla (se entregan con `json_script`, que los escapa)."""
    if not resultado or not resultado.grafico or not resultado.grafico.etiquetas:
        return None
    grafico = resultado.grafico
    return {
        "titulo": grafico.titulo,
        "etiquetas": grafico.etiquetas,
        "series": [{"nombre": nombre, "valores": valores} for nombre, valores in grafico.series],
        "horizontal": grafico.horizontal,
        "colores": exportadores.COLORES_SERIES,
        "alto": 80 + 34 * len(grafico.etiquetas) if grafico.horizontal else 320,
    }


# ---------------------------------------------------------------------------
# Configuración (solo Administrador)
# ---------------------------------------------------------------------------


class MixinAdministrarReportes(ModuloHabilitadoMixin, RolRequeridoMixin):
    codigo_modulo = Modulo.MOD10_REPORTES
    roles_permitidos = (Rol.ADMINISTRADOR,)


class VisibilidadReportesView(MixinAdministrarReportes, View):
    """Qué roles ven cada reporte; el Administrador los ve todos."""

    template_name = "reportes/visibilidad.html"

    def get(self, request):
        roles, filas = selectores.matriz_visibilidad()
        return render(request, self.template_name, {"roles": roles, "filas": filas})

    def post(self, request):
        habilitados = set()
        for clave in request.POST:
            if clave.startswith("visible_"):
                try:
                    _, id_reporte, id_rol = clave.split("_")
                    habilitados.add((int(id_reporte), int(id_rol)))
                except ValueError:
                    continue
        servicios.guardar_visibilidad(habilitados)
        messages.success(request, "Se guardó la visibilidad de los reportes por rol.")
        return redirect("reportes:visibilidad")


class FiltroDescargasForm(FormularioBase):
    reporte = forms.ModelChoiceField(
        required=False, label="Reporte", queryset=Reporte.objects.all(), empty_label="Todos"
    )
    usuario = forms.ModelChoiceField(
        required=False, label="Usuario", queryset=Usuario.objects.all(), empty_label="Todos"
    )
    desde = forms.DateField(required=False, label="Desde", widget=forms.DateInput(attrs={"type": "date"}))
    hasta = forms.DateField(required=False, label="Hasta", widget=forms.DateInput(attrs={"type": "date"}))


class DescargasReportesView(MixinAdministrarReportes, ListView):
    """Historial de descargas: reporte, usuario, fecha, formato y filtros usados (HU028-5)."""

    template_name = "reportes/descargas.html"
    context_object_name = "descargas"
    paginate_by = 30

    def get_queryset(self):
        self.formulario_filtro = FiltroDescargasForm(self.request.GET or None)
        filtros = self.formulario_filtro.cleaned_data if self.formulario_filtro.is_valid() else {}
        return selectores.descargas(**filtros)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["formulario_filtro"] = self.formulario_filtro
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto
