"""
Vistas del módulo 9: expediente y bitácora por cliente.

Permisos (HU025-HU027 y decisiones de sesión del 1-oct-2026):
- Los tres roles consultan el expediente, descargan adjuntos y registran
  anotaciones; el Contador Junior solo sobre sus clientes asignados.
- Nadie edita ni elimina una anotación guardada (bitácora inmutable).
- Solo el Administrador archiva o restaura anotaciones. Las archivadas se
  ocultan por defecto, pero cualquier rol puede verlas con el filtro.
"""

from django.contrib import messages
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView, View

from aplicaciones.comunes.models import Adjunto
from aplicaciones.seguridad.models import Modulo, Rol
from aplicaciones.seguridad.permisos import ModuloHabilitadoMixin, RolRequeridoMixin

from . import selectores, servicios
from .formularios import AnotacionForm, FiltroAnotacionesForm


def _es_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _redirigir_o_recargar(request, url):
    """Redirige de forma normal, o fuerza la recarga cuando la petición es AJAX."""
    if _es_ajax(request):
        return HttpResponse(f'<script>window.location.href = "{url}";</script>', content_type="text/html")
    return redirect(url)


def _adjunto_visible_o_404(usuario, pk):
    """Adjunto de una anotación de un cliente visible para el usuario (protege contra IDOR)."""
    adjunto = get_object_or_404(Adjunto, pk=pk, tabla_origen=Adjunto.ANOTACION)
    get_object_or_404(selectores.anotaciones_visibles(usuario), pk=adjunto.id_origen)
    return adjunto


class ListaAnotacionesView(ModuloHabilitadoMixin, ListView):
    """
    Bitácora general: anotaciones de todos los clientes visibles, con filtro
    por cliente, tipo y rango de fechas (acceso desde el menú y el panel).
    """

    codigo_modulo = Modulo.MOD09_EXPEDIENTE
    template_name = "expediente/lista.html"
    context_object_name = "anotaciones"
    paginate_by = 20
    cliente = None

    def obtener_cliente(self):
        return None

    def get_queryset(self):
        self.cliente = self.obtener_cliente()
        self.formulario_filtro = FiltroAnotacionesForm(self.request.GET or None, usuario=self.request.user)
        filtros = {}
        if self.formulario_filtro.is_valid():
            filtros = dict(self.formulario_filtro.cleaned_data)
        if self.cliente:
            filtros["cliente"] = self.cliente
        return selectores.filtrar_anotaciones(
            self.request.user,
            cliente=filtros.get("cliente"),
            tipo=filtros.get("tipo"),
            desde=filtros.get("desde"),
            hasta=filtros.get("hasta"),
            incluir_archivadas=filtros.get("incluir_archivadas", False),
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["anotaciones"] = selectores.con_adjuntos(contexto["anotaciones"])
        contexto["cliente"] = self.cliente
        contexto["formulario_filtro"] = self.formulario_filtro
        contexto["tipos_anotacion"] = selectores.tipos_de_anotacion(self.request.user)
        contexto["es_administrador"] = self.request.user.es_administrador
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto


class ExpedienteClienteView(ListaAnotacionesView):
    """Expediente completo de un cliente (acceso desde su ficha y el tablero Kanban)."""

    def obtener_cliente(self):
        return get_object_or_404(
            selectores.clientes_visibles(self.request.user), pk=self.kwargs["pk_cliente"]
        )


class CrearAnotacionView(ModuloHabilitadoMixin, View):
    """Registra una anotación con sus archivos de soporte."""

    codigo_modulo = Modulo.MOD09_EXPEDIENTE

    def _template(self, request):
        return (
            "expediente/anotacion_form_modal.html" if _es_ajax(request) else "expediente/anotacion_form.html"
        )

    def _contexto(self, request, formulario):
        return {"formulario": formulario, "tipos_anotacion": selectores.tipos_de_anotacion(request.user)}

    def get(self, request):
        inicial = {}
        if request.GET.get("cliente"):
            inicial["cliente"] = request.GET["cliente"]
        formulario = AnotacionForm(usuario=request.user, initial=inicial)
        return render(request, self._template(request), self._contexto(request, formulario))

    def post(self, request):
        formulario = AnotacionForm(request.POST, request.FILES, usuario=request.user)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            anotacion = servicios.crear_anotacion(
                cliente=datos["cliente"],
                usuario=request.user,
                tipo_anotacion=datos["tipo_anotacion"],
                fecha=datos["fecha"],
                contenido=datos["contenido"],
                archivos=datos["archivos"],
            )
            messages.success(request, "La anotación se registró en el expediente.")
            url = reverse("expediente:cliente", kwargs={"pk_cliente": anotacion.cliente_id})
            return _redirigir_o_recargar(request, url)
        return render(request, self._template(request), self._contexto(request, formulario))


class ArchivarAnotacionView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Archiva o restaura una anotación (solo el Administrador)."""

    codigo_modulo = Modulo.MOD09_EXPEDIENTE
    roles_permitidos = (Rol.ADMINISTRADOR,)
    restaurar = False

    def post(self, request, pk):
        anotacion = get_object_or_404(selectores.anotaciones_visibles(request.user), pk=pk)
        if self.restaurar:
            servicios.restaurar_anotacion(anotacion)
            messages.success(request, "La anotación volvió al expediente.")
        else:
            servicios.archivar_anotacion(anotacion)
            messages.success(request, "La anotación se archivó; se conserva en el historial.")
        url = reverse("expediente:cliente", kwargs={"pk_cliente": anotacion.cliente_id})
        return _redirigir_o_recargar(request, url)


class DescargarAdjuntoAnotacionView(ModuloHabilitadoMixin, View):
    """Descarga un archivo de soporte de una anotación visible para el usuario."""

    codigo_modulo = Modulo.MOD09_EXPEDIENTE

    def get(self, request, pk):
        adjunto = _adjunto_visible_o_404(request.user, pk)
        return FileResponse(adjunto.archivo.open("rb"), as_attachment=True, filename=adjunto.nombre_archivo)
