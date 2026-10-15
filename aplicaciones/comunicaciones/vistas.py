"""
Vistas del módulo 7: comunicaciones integradas.

Permisos (HU019-HU021):
- Los tres roles consultan el historial; el Contador Junior solo el de sus
  clientes asignados.
- Solo el Administrador y el Contador Senior registran comunicaciones
  manuales; el Junior solo consulta.
- Nadie edita ni elimina comunicaciones del historial.
"""

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView, View

from aplicaciones.comunes.paginacion import PaginacionMixin
from aplicaciones.seguridad.models import Modulo, Rol
from aplicaciones.seguridad.permisos import ModuloHabilitadoMixin, RolRequeridoMixin

from . import selectores, servicios
from .formularios import ComunicacionManualForm, FiltroComunicacionesForm

ROLES_REGISTRAN = (Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR)


def _es_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _redirigir_o_recargar(request, url):
    """Redirige de forma normal, o fuerza la recarga cuando la petición es AJAX."""
    if _es_ajax(request):
        return HttpResponse(f'<script>window.location.href = "{url}";</script>', content_type="text/html")
    return redirect(url)


class ListaComunicacionesView(ModuloHabilitadoMixin, PaginacionMixin, ListView):
    """Historial general de comunicaciones de los clientes visibles (acceso desde el menú)."""

    codigo_modulo = Modulo.MOD07_COMUNICACIONES
    template_name = "comunicaciones/lista.html"
    context_object_name = "comunicaciones"
    cliente = None

    def obtener_cliente(self):
        return None

    def get_queryset(self):
        self.cliente = self.obtener_cliente()
        self.formulario_filtro = FiltroComunicacionesForm(self.request.GET or None, usuario=self.request.user)
        filtros = {}
        if self.formulario_filtro.is_valid():
            filtros = dict(self.formulario_filtro.cleaned_data)
        if self.cliente:
            filtros["cliente"] = self.cliente
        return selectores.filtrar_comunicaciones(
            self.request.user,
            cliente=filtros.get("cliente"),
            canal=filtros.get("canal"),
            tipo=filtros.get("tipo"),
            desde=filtros.get("desde"),
            hasta=filtros.get("hasta"),
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["cliente"] = self.cliente
        contexto["formulario_filtro"] = self.formulario_filtro
        contexto["puede_registrar"] = self.request.user.rol.nombre_rol in ROLES_REGISTRAN
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto


class ComunicacionesClienteView(ListaComunicacionesView):
    """Historial de comunicaciones de un cliente (acceso desde su ficha)."""

    def obtener_cliente(self):
        return get_object_or_404(
            selectores.clientes_visibles(self.request.user), pk=self.kwargs["pk_cliente"]
        )


class RegistrarComunicacionView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Registro manual de una llamada, reunión u otro contacto (Administrador y Senior)."""

    codigo_modulo = Modulo.MOD07_COMUNICACIONES
    roles_permitidos = ROLES_REGISTRAN

    def _template(self, request):
        if _es_ajax(request):
            return "comunicaciones/comunicacion_form_modal.html"
        return "comunicaciones/comunicacion_form.html"

    def _contexto(self, request, formulario):
        return {"formulario": formulario, "canales": selectores.canales(request.user)}

    def get(self, request):
        inicial = {}
        if request.GET.get("cliente"):
            inicial["cliente"] = request.GET["cliente"]
        formulario = ComunicacionManualForm(usuario=request.user, initial=inicial)
        return render(request, self._template(request), self._contexto(request, formulario))

    def post(self, request):
        formulario = ComunicacionManualForm(request.POST, usuario=request.user)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            comunicacion = servicios.registrar_comunicacion_manual(
                cliente=datos["cliente"],
                usuario=request.user,
                canal=datos["canal"],
                fecha_hora=datos["fecha_hora"],
                contenido_resumen=datos["contenido_resumen"],
            )
            messages.success(request, "La comunicación se registró en el historial del cliente.")
            url = reverse("comunicaciones:cliente", kwargs={"pk_cliente": comunicacion.cliente_id})
            return _redirigir_o_recargar(request, url)
        return render(request, self._template(request), self._contexto(request, formulario))
