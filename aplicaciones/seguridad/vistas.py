"""Vistas del módulo 8: inicio de sesión, cierre de sesión y panel principal."""

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .models import Modulo

Usuario = get_user_model()

# Rutas de los módulos ya construidos. A medida que se desarrolla cada módulo
# se agrega aquí su ruta para que la tarjeta del panel quede navegable.
RUTAS_MODULOS = {
    Modulo.MOD01_CLIENTES: "clientes:lista",
}


class IniciarSesionView(LoginView):
    """Formulario de acceso al sistema (CU001)."""

    template_name = "seguridad/iniciar_sesion.html"
    redirect_authenticated_user = True


class CerrarSesionView(LogoutView):
    """Cierra la sesión activa y regresa al inicio de sesión."""

    next_page = reverse_lazy("seguridad:iniciar_sesion")


class PanelView(LoginRequiredMixin, TemplateView):
    """
    Panel principal del sistema.

    Muestra al usuario únicamente los módulos que su rol tiene habilitados
    según la configuración de permiso_rol_modulo (RQF031).
    """

    template_name = "seguridad/panel.html"

    def get_context_data(self, **kwargs):
        from aplicaciones.clientes.models import Cliente, ClienteServicio

        contexto = super().get_context_data(**kwargs)
        usuario = self.request.user
        contexto["modulos"] = [
            {"modulo": modulo, "url": RUTAS_MODULOS.get(modulo.codigo_modulo)}
            for modulo in Modulo.objects.all()
            if usuario.tiene_modulo_habilitado(modulo.codigo_modulo)
        ]
        contexto["indicadores"] = [
            {
                "etiqueta": "Clientes activos",
                "valor": Cliente.objects.filter(estado=Cliente.ACTIVO).count(),
                "color": "c-green",
            },
            {
                "etiqueta": "Clientes inactivos",
                "valor": Cliente.objects.filter(estado=Cliente.INACTIVO).count(),
                "color": "c-text",
            },
            {
                "etiqueta": "Servicios registrados",
                "valor": ClienteServicio.objects.count(),
                "color": "c-teal",
            },
            {
                "etiqueta": "Usuarios del equipo",
                "valor": Usuario.objects.filter(estado=Usuario.ACTIVO).count(),
                "color": "c-orange",
            },
        ]
        return contexto
