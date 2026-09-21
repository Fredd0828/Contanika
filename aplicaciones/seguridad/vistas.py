"""Vistas del módulo 8: inicio de sesión, cierre de sesión y panel principal."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .models import Modulo


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
        contexto = super().get_context_data(**kwargs)
        usuario = self.request.user
        contexto["modulos"] = [
            modulo for modulo in Modulo.objects.all() if usuario.tiene_modulo_habilitado(modulo.codigo_modulo)
        ]
        return contexto
