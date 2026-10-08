"""
Vistas del módulo 5: hallazgos y revisiones contables.

Permisos (decisión de sesión, el spec no los detalla para este módulo):
- Todos los roles consultan, registran, editan y cambian el estado de los
  hallazgos; el Contador Junior solo lo hace sobre los de sus clientes
  asignados (mismo criterio que Documentos y Calendario).
- Administrador y Contador Senior son los únicos que eliminan un hallazgo
  completo (mismo criterio que Documentos y Tareas).
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
from .formularios import (
    AdjuntoHallazgoForm,
    CambiarEstadoHallazgoForm,
    FiltroHallazgosForm,
    HallazgoForm,
)
from .models import Hallazgo

ROLES_ELIMINAN = (Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR)


def _es_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _redirigir_o_recargar(request, nombre_ruta, **kwargs):
    """Redirige de forma normal, o fuerza la recarga cuando la petición es AJAX."""
    url = reverse(nombre_ruta, kwargs=kwargs)
    if _es_ajax(request):
        return HttpResponse(f'<script>window.location.href = "{url}";</script>', content_type="text/html")
    return redirect(url)


def _adjunto_visible_o_404(usuario, pk):
    """Adjunto de un hallazgo visible para el usuario (protege contra IDOR)."""
    adjunto = get_object_or_404(Adjunto, pk=pk, tabla_origen=Adjunto.HALLAZGO)
    get_object_or_404(selectores.hallazgos_visibles(usuario), pk=adjunto.id_origen)
    return adjunto


def _adjunto_gestionable_o_404(usuario, pk):
    """Adjunto de un hallazgo que el usuario puede modificar (el Junior, solo de sus clientes)."""
    adjunto = get_object_or_404(Adjunto, pk=pk, tabla_origen=Adjunto.HALLAZGO)
    get_object_or_404(selectores.hallazgos_gestionables(usuario), pk=adjunto.id_origen)
    return adjunto


class ListaHallazgosView(ModuloHabilitadoMixin, ListView):
    """Listado filtrable de hallazgos y revisiones."""

    codigo_modulo = Modulo.MOD05_HALLAZGOS
    template_name = "hallazgos/lista.html"
    context_object_name = "hallazgos"
    paginate_by = 20

    def get_queryset(self):
        opciones = selectores.opciones_filtro_hallazgos(self.request.user)
        self.formulario_filtro = FiltroHallazgosForm(
            self.request.GET or None, usuario=self.request.user, opciones=opciones
        )
        tipo = estado = responsable = desde = hasta = None
        if self.formulario_filtro.is_valid():
            tipo = self.formulario_filtro.cleaned_data.get("tipo")
            estado = self.formulario_filtro.cleaned_data.get("estado")
            responsable = self.formulario_filtro.cleaned_data.get("responsable")
            desde = self.formulario_filtro.cleaned_data.get("desde")
            hasta = self.formulario_filtro.cleaned_data.get("hasta")
        return selectores.filtrar_hallazgos(
            self.request.user, tipo=tipo, estado=estado, responsable=responsable, desde=desde, hasta=hasta
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["formulario_filtro"] = self.formulario_filtro
        contexto["opciones"] = selectores.opciones_filtro_hallazgos(self.request.user)
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto


class DetalleHallazgoView(ModuloHabilitadoMixin, View):
    """Detalle del hallazgo: edición, cambio de estado y adjuntos de soporte."""

    codigo_modulo = Modulo.MOD05_HALLAZGOS

    def _template(self, request):
        if _es_ajax(request):
            return "hallazgos/hallazgo_detalle_modal.html"
        return "hallazgos/hallazgo_detalle.html"

    def get(self, request, pk):
        hallazgo = get_object_or_404(selectores.hallazgos_visibles(request.user), pk=pk)
        puede_eliminar = request.user.rol.nombre_rol in ROLES_ELIMINAN
        contexto = {
            "hallazgo": hallazgo,
            "adjuntos": selectores.adjuntos_del_hallazgo(hallazgo),
            "puede_eliminar": puede_eliminar,
            "puede_gestionar": selectores.hallazgos_gestionables(request.user)
            .filter(pk=hallazgo.pk)
            .exists(),
            "formulario": HallazgoForm(instance=hallazgo, usuario=request.user),
            "formulario_estado": CambiarEstadoHallazgoForm(initial={"estado": hallazgo.estado}),
            "formulario_adjunto": AdjuntoHallazgoForm(),
        }
        return render(request, self._template(request), contexto)


class CrearHallazgoView(ModuloHabilitadoMixin, View):
    """Registra un nuevo hallazgo (cliente restringido para el Contador Junior)."""

    codigo_modulo = Modulo.MOD05_HALLAZGOS

    def _template(self, request):
        return "hallazgos/hallazgo_form_modal.html" if _es_ajax(request) else "hallazgos/hallazgo_form.html"

    def get(self, request):
        inicial = {}
        if request.GET.get("cliente"):
            inicial["cliente"] = request.GET["cliente"]
        return render(
            request,
            self._template(request),
            {
                "formulario": HallazgoForm(usuario=request.user, initial=inicial),
                "accion": "crear",
                "opciones": selectores.opciones_filtro_hallazgos(request.user),
            },
        )

    def post(self, request):
        formulario = HallazgoForm(request.POST, usuario=request.user)
        if formulario.is_valid():
            servicios.crear_hallazgo(formulario)
            messages.success(request, "El hallazgo se registró correctamente.")
            return _redirigir_o_recargar(request, "hallazgos:lista")
        return render(
            request,
            self._template(request),
            {
                "formulario": formulario,
                "accion": "crear",
                "opciones": selectores.opciones_filtro_hallazgos(request.user),
            },
        )


class EditarHallazgoView(ModuloHabilitadoMixin, View):
    """Edita los datos de registro de un hallazgo visible para el usuario."""

    codigo_modulo = Modulo.MOD05_HALLAZGOS

    def _template(self, request):
        return "hallazgos/hallazgo_form_modal.html" if _es_ajax(request) else "hallazgos/hallazgo_form.html"

    def get(self, request, pk):
        hallazgo = get_object_or_404(selectores.hallazgos_gestionables(request.user), pk=pk)
        return render(
            request,
            self._template(request),
            {
                "formulario": HallazgoForm(instance=hallazgo, usuario=request.user),
                "accion": "editar",
                "hallazgo": hallazgo,
                "opciones": selectores.opciones_filtro_hallazgos(request.user),
            },
        )

    def post(self, request, pk):
        hallazgo = get_object_or_404(selectores.hallazgos_gestionables(request.user), pk=pk)
        formulario = HallazgoForm(request.POST, instance=hallazgo, usuario=request.user)
        if formulario.is_valid():
            servicios.actualizar_hallazgo(hallazgo, formulario)
            messages.success(request, "El hallazgo se actualizó correctamente.")
            return _redirigir_o_recargar(request, "hallazgos:detalle", pk=hallazgo.pk)
        return render(
            request,
            self._template(request),
            {
                "formulario": formulario,
                "accion": "editar",
                "hallazgo": hallazgo,
                "opciones": selectores.opciones_filtro_hallazgos(request.user),
            },
        )


class EliminarHallazgoView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Elimina un hallazgo y sus adjuntos (Administrador y Contador Senior)."""

    codigo_modulo = Modulo.MOD05_HALLAZGOS
    roles_permitidos = ROLES_ELIMINAN

    def post(self, request, pk):
        hallazgo = get_object_or_404(Hallazgo, pk=pk)
        servicios.eliminar_hallazgo(hallazgo)
        messages.success(request, "El hallazgo se eliminó correctamente.")
        return _redirigir_o_recargar(request, "hallazgos:lista")


class CambiarEstadoHallazgoView(ModuloHabilitadoMixin, View):
    """Cambia el estado de un hallazgo visible para el usuario."""

    codigo_modulo = Modulo.MOD05_HALLAZGOS

    def post(self, request, pk):
        hallazgo = get_object_or_404(selectores.hallazgos_gestionables(request.user), pk=pk)
        formulario = CambiarEstadoHallazgoForm(request.POST)
        if formulario.is_valid():
            servicios.cambiar_estado_hallazgo(
                hallazgo,
                formulario.cleaned_data["estado"],
                formulario.cleaned_data["observacion_cierre"],
            )
            messages.success(request, "El estado del hallazgo se actualizó.")
        else:
            for error in formulario.non_field_errors():
                messages.error(request, error)
        return _redirigir_o_recargar(request, "hallazgos:detalle", pk=hallazgo.pk)


class AgregarAdjuntoHallazgoView(ModuloHabilitadoMixin, View):
    """Agrega un archivo de soporte a un hallazgo visible para el usuario."""

    codigo_modulo = Modulo.MOD05_HALLAZGOS

    def post(self, request, pk):
        hallazgo = get_object_or_404(selectores.hallazgos_gestionables(request.user), pk=pk)
        formulario = AdjuntoHallazgoForm(request.POST, request.FILES)
        if formulario.is_valid():
            servicios.agregar_adjunto(hallazgo, formulario.cleaned_data["archivo"])
            messages.success(request, "El adjunto se cargó correctamente.")
        else:
            for error in formulario.errors.get("archivo", []):
                messages.error(request, error)
        return _redirigir_o_recargar(request, "hallazgos:detalle", pk=hallazgo.pk)


class EliminarAdjuntoHallazgoView(ModuloHabilitadoMixin, View):
    """Elimina un adjunto de un hallazgo visible para el usuario."""

    codigo_modulo = Modulo.MOD05_HALLAZGOS

    def post(self, request, pk):
        adjunto = _adjunto_gestionable_o_404(request.user, pk)
        id_hallazgo = adjunto.id_origen
        servicios.eliminar_adjunto(adjunto)
        messages.success(request, "El adjunto se eliminó correctamente.")
        return _redirigir_o_recargar(request, "hallazgos:detalle", pk=id_hallazgo)


class DescargarAdjuntoHallazgoView(ModuloHabilitadoMixin, View):
    """Descarga el archivo de soporte de un hallazgo visible para el usuario."""

    codigo_modulo = Modulo.MOD05_HALLAZGOS

    def get(self, request, pk):
        adjunto = _adjunto_visible_o_404(request.user, pk)
        return FileResponse(adjunto.archivo.open("rb"), as_attachment=True, filename=adjunto.nombre_archivo)
