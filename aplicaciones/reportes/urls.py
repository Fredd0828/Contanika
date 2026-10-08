"""Rutas del módulo 10: reportes y análisis."""

from django.urls import path

from . import vistas

app_name = "reportes"
urlpatterns = [
    path("reportes/", vistas.InicioReportesView.as_view(), name="inicio"),
    path("reportes/visibilidad/", vistas.VisibilidadReportesView.as_view(), name="visibilidad"),
    path("reportes/descargas/", vistas.DescargasReportesView.as_view(), name="descargas"),
    path("reportes/<slug:slug>/", vistas.ReporteView.as_view(), name="reporte"),
]
