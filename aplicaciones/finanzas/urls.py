"""Rutas del módulo 6: honorarios, cartera y cuentas de cobro."""

from django.urls import path

from . import vistas

app_name = "finanzas"

urlpatterns = [
    path("honorarios/", vistas.HistoricoCuentasCobroView.as_view(), name="historico"),
    path("honorarios/cuentas-cobro/generar/", vistas.GenerarCuentaCobroView.as_view(), name="generar"),
    path("honorarios/cuentas-cobro/<int:pk>/", vistas.DetalleCuentaCobroView.as_view(), name="detalle"),
    path(
        "honorarios/cuentas-cobro/<int:pk>/descargar/",
        vistas.DescargarCuentaCobroView.as_view(),
        name="descargar",
    ),
    path(
        "honorarios/cuentas-cobro/<int:pk>/eliminar/",
        vistas.EliminarCuentaCobroView.as_view(),
        name="eliminar",
    ),
    path(
        "honorarios/clientes/<int:pk>/honorario/",
        vistas.ConfigurarHonorarioView.as_view(),
        name="honorario",
    ),
    path("honorarios/catalogos/", vistas.CatalogosView.as_view(), name="catalogos"),
    path(
        "honorarios/catalogos/<str:catalogo>/nuevo/",
        vistas.ElementoCatalogoView.as_view(),
        name="catalogo_crear",
    ),
    path(
        "honorarios/catalogos/<str:catalogo>/<int:pk>/editar/",
        vistas.ElementoCatalogoView.as_view(),
        name="catalogo_editar",
    ),
    path(
        "honorarios/catalogos/<str:catalogo>/<int:pk>/eliminar/",
        vistas.EliminarElementoCatalogoView.as_view(),
        name="catalogo_eliminar",
    ),
    # Envíos (HU045-HU047) y programación
    path(
        "honorarios/cuentas-cobro/<int:pk>/enviar/",
        vistas.EnviarCuentaCobroView.as_view(),
        name="enviar",
    ),
    path("honorarios/envio-masivo/", vistas.EnvioMasivoView.as_view(), name="envio_masivo"),
    path(
        "honorarios/envio-masivo/resumen/",
        vistas.ResumenEnvioMasivoView.as_view(),
        name="envio_masivo_resumen",
    ),
    path("honorarios/whatsapp-pendientes/", vistas.BandejaWhatsappView.as_view(), name="bandeja_whatsapp"),
    path("honorarios/envios/", vistas.EnviosProgramadosView.as_view(), name="programados"),
    path("honorarios/envios/<int:pk>/whatsapp/", vistas.AbrirWhatsappView.as_view(), name="abrir_whatsapp"),
    path("honorarios/envios/<int:pk>/reintentar/", vistas.ReintentarEnvioView.as_view(), name="reintentar"),
    path("honorarios/envios/<int:pk>/cancelar/", vistas.CancelarEnvioView.as_view(), name="cancelar_envio"),
    path("honorarios/configuracion/", vistas.ConfiguracionCobroView.as_view(), name="configuracion"),
    path(
        "honorarios/configuracion/ejecutar/",
        vistas.EjecutarProcesoCobroView.as_view(),
        name="ejecutar_proceso",
    ),
    path("cuenta-cobro/<str:token>/", vistas.PdfPublicoView.as_view(), name="pdf_publico"),
]
