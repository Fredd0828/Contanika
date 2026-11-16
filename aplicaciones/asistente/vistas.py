"""
Vistas del asistente de consultas.

- La página del asistente muestra las preguntas sugeridas (solo las de los
  módulos habilitados para el rol) y las dudas de uso frecuentes.
- Las respuestas se piden por AJAX y vuelven como un fragmento HTML que la
  página agrega a la conversación.
- Todo es de solo lectura: el asistente no modifica datos ni usa servicios
  externos.
"""

from django.http import Http404
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView

from aplicaciones.seguridad import guias
from aplicaciones.seguridad.models import Modulo
from aplicaciones.seguridad.permisos import ModuloHabilitadoMixin

from . import consultas


class AsistenteView(ModuloHabilitadoMixin, TemplateView):
    """Página del asistente con las preguntas sugeridas y las dudas de uso."""

    codigo_modulo = Modulo.SEC_ASISTENTE
    template_name = "asistente/inicio.html"

    def get_context_data(self, **kwargs):
        usuario = self.request.user
        contexto = super().get_context_data(**kwargs)
        contexto["consultas"] = [
            {"consulta": consulta, "clientes": consulta.opciones_cliente(usuario)}
            for consulta in consultas.consultas_visibles(usuario)
        ]
        contexto["preguntas_frecuentes"] = guias.PREGUNTAS_FRECUENTES
        return contexto


class ConsultarView(ModuloHabilitadoMixin, View):
    """Responde una pregunta sugerida y devuelve el fragmento con la respuesta."""

    codigo_modulo = Modulo.SEC_ASISTENTE

    def post(self, request, slug):
        consulta = consultas.obtener_visible(request.user, slug)
        if consulta is None:
            raise Http404("La consulta no existe o no está habilitada para su rol.")
        try:
            respuesta = consultas.ejecutar(request.user, consulta, request.POST.get("cliente"))
        except consultas.ClienteNoPermitido:
            return render(
                request,
                "asistente/_mensaje.html",
                {"texto": "Elija un cliente de la lista para hacer esta consulta.", "error": True},
                status=400,
            )
        return render(request, "asistente/_respuesta.html", {"respuesta": respuesta})
