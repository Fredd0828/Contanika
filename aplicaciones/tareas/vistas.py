"""
Vistas del módulo 3: tablero de tareas Kanban.

Permisos (especificaciones del Módulo 3):
- Todos los roles consultan el tablero; el Contador Junior solo ve las
  tareas asignadas a él.
- Administrador y Contador Senior crean, editan o eliminan cualquier tarea.
- El Contador Junior únicamente cambia el estado de sus tareas asignadas y
  registra observaciones de avance sobre ellas.
"""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import View

from aplicaciones.seguridad.models import Modulo, Rol
from aplicaciones.seguridad.permisos import ModuloHabilitadoMixin, RolRequeridoMixin

from .formularios import (
    CambiarEstadoTareaForm,
    FiltroTareasForm,
    ObservacionTareaForm,
    TareaForm,
)
from .models import Tarea
from .selectores import (
    agrupar_por_estado,
    filtrar_tareas,
    notificaciones_usuario,
    opciones_filtro_tareas,
    puede_actualizar_tarea,
    tareas_visibles,
)
from .servicios import (
    actualizar_tarea,
    agregar_observacion,
    cambiar_estado_tarea,
    crear_tarea,
    eliminar_tarea,
)

ROLES_EDITAN = (Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR)


def _es_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _redirigir_o_recargar(request, nombre_ruta, **kwargs):
    """Redirige de forma normal, o fuerza la recarga cuando la petición es AJAX."""
    url = reverse(nombre_ruta, kwargs=kwargs)
    if _es_ajax(request):
        return HttpResponse(f'<script>window.location.href = "{url}";</script>', content_type="text/html")
    return redirect(url)


class TableroTareasView(ModuloHabilitadoMixin, View):
    """Tablero Kanban: columnas Por hacer / En progreso / En revisión / Terminado."""

    codigo_modulo = Modulo.MOD03_TAREAS
    template_name = "tareas/tablero.html"

    def get(self, request):
        parametros = request.GET
        opciones = opciones_filtro_tareas(request.user)
        tareas = filtrar_tareas(
            request.user,
            cliente=parametros.get("cliente") or None,
            responsable=parametros.get("responsable") or None,
            prioridad=parametros.get("prioridad") or None,
            tipo_tarea=parametros.get("tipo_tarea") or None,
        )
        columnas = agrupar_por_estado(tareas)
        puede_editar = request.user.rol.nombre_rol in ROLES_EDITAN
        contexto = {
            "tablero": [(estado, etiqueta, columnas[estado]) for estado, etiqueta in Tarea.OPCIONES_ESTADO],
            "formulario_filtro": FiltroTareasForm(
                parametros or None, usuario=request.user, opciones=opciones
            ),
            "puede_editar": puede_editar,
            "formulario_crear": TareaForm(usuario=request.user) if puede_editar else None,
            "opciones": opciones,
        }
        return render(request, self.template_name, contexto)


class DetalleTareaView(ModuloHabilitadoMixin, View):
    """
    Tarjeta expandida de la tarea: edición (Admin/Senior), cambio de estado,
    observaciones de avance, historial de cambios y acceso al expediente.
    """

    codigo_modulo = Modulo.MOD03_TAREAS

    def _template(self, request):
        return "tareas/tarea_detalle_modal.html" if _es_ajax(request) else "tareas/tarea_detalle.html"

    def get(self, request, pk):
        tarea = get_object_or_404(
            tareas_visibles(request.user).prefetch_related("historial__usuario", "observaciones__usuario"),
            pk=pk,
        )
        puede_editar = request.user.rol.nombre_rol in ROLES_EDITAN
        contexto = {
            "tarea": tarea,
            "puede_editar": puede_editar,
            "formulario": TareaForm(instance=tarea, usuario=request.user) if puede_editar else None,
            "formulario_estado": CambiarEstadoTareaForm(initial={"estado": tarea.estado}),
            "formulario_observacion": ObservacionTareaForm(),
            "puede_actualizar": puede_actualizar_tarea(request.user, tarea),
        }
        return render(request, self._template(request), contexto)


class CrearTareaView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Crea una nueva tarjeta del tablero (Administrador y Contador Senior)."""

    codigo_modulo = Modulo.MOD03_TAREAS
    roles_permitidos = ROLES_EDITAN

    def _template(self, request):
        return "tareas/tarea_form_modal.html" if _es_ajax(request) else "tareas/tarea_form.html"

    def get(self, request):
        inicial = {}
        if request.GET.get("cliente"):
            inicial["cliente"] = request.GET["cliente"]
        return render(
            request,
            self._template(request),
            {
                "formulario": TareaForm(usuario=request.user, initial=inicial),
                "accion": "crear",
                "opciones": opciones_filtro_tareas(request.user),
            },
        )

    def post(self, request):
        formulario = TareaForm(request.POST, usuario=request.user)
        if formulario.is_valid():
            crear_tarea(formulario)
            messages.success(request, "La tarea se creó correctamente.")
            return _redirigir_o_recargar(request, "tareas:tablero")
        return render(
            request,
            self._template(request),
            {"formulario": formulario, "accion": "crear", "opciones": opciones_filtro_tareas(request.user)},
        )


class EditarTareaView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Edita una tarea existente (Administrador y Contador Senior)."""

    codigo_modulo = Modulo.MOD03_TAREAS
    roles_permitidos = ROLES_EDITAN

    def _template(self, request):
        return "tareas/tarea_form_modal.html" if _es_ajax(request) else "tareas/tarea_form.html"

    def get(self, request, pk):
        tarea = get_object_or_404(Tarea, pk=pk)
        return render(
            request,
            self._template(request),
            {
                "formulario": TareaForm(instance=tarea, usuario=request.user),
                "accion": "editar",
                "tarea": tarea,
                "opciones": opciones_filtro_tareas(request.user),
            },
        )

    def post(self, request, pk):
        tarea = get_object_or_404(Tarea, pk=pk)
        formulario = TareaForm(request.POST, instance=tarea, usuario=request.user)
        if formulario.is_valid():
            actualizar_tarea(tarea, formulario)
            messages.success(request, "La tarea se actualizó correctamente.")
            return _redirigir_o_recargar(request, "tareas:tablero")
        return render(
            request,
            self._template(request),
            {
                "formulario": formulario,
                "accion": "editar",
                "tarea": tarea,
                "opciones": opciones_filtro_tareas(request.user),
            },
        )


class EliminarTareaView(ModuloHabilitadoMixin, RolRequeridoMixin, View):
    """Elimina una tarea del tablero (operación irreversible)."""

    codigo_modulo = Modulo.MOD03_TAREAS
    roles_permitidos = ROLES_EDITAN

    def post(self, request, pk):
        tarea = get_object_or_404(Tarea, pk=pk)
        eliminar_tarea(tarea)
        messages.success(request, "La tarea se eliminó correctamente.")
        return _redirigir_o_recargar(request, "tareas:tablero")


class CambiarEstadoTareaView(ModuloHabilitadoMixin, View):
    """
    Cambia el estado de una tarea, por arrastre (AJAX) o por el selector de
    la tarjeta. El Contador Junior solo puede mover sus propias tareas.
    """

    codigo_modulo = Modulo.MOD03_TAREAS

    def post(self, request, pk):
        tarea = get_object_or_404(tareas_visibles(request.user), pk=pk)
        formulario = CambiarEstadoTareaForm(request.POST)
        ajax = _es_ajax(request)

        if not formulario.is_valid():
            if ajax:
                return JsonResponse({"ok": False, "error": "Estado no válido."}, status=400)
            messages.error(request, "Estado no válido.")
            return redirect("tareas:tablero")

        try:
            cambiar_estado_tarea(tarea, formulario.cleaned_data["estado"], request.user)
        except PermissionDenied as error:
            if ajax:
                return JsonResponse({"ok": False, "error": str(error)}, status=403)
            messages.error(request, str(error))
            return redirect("tareas:tablero")

        if ajax:
            return JsonResponse({"ok": True, "estado": tarea.estado})
        messages.success(request, "El estado de la tarea se actualizó.")
        return redirect("tareas:tablero")


class AgregarObservacionView(ModuloHabilitadoMixin, View):
    """Registra una observación de avance sobre una tarea visible para el usuario."""

    codigo_modulo = Modulo.MOD03_TAREAS

    def post(self, request, pk):
        tarea = get_object_or_404(tareas_visibles(request.user), pk=pk)
        if not puede_actualizar_tarea(request.user, tarea):
            messages.error(request, "Solo puede agregar observaciones a las tareas asignadas a usted.")
            return _redirigir_o_recargar(request, "tareas:detalle", pk=tarea.pk)
        formulario = ObservacionTareaForm(request.POST)
        if formulario.is_valid():
            agregar_observacion(tarea, request.user, formulario.cleaned_data["contenido"])
            messages.success(request, "La observación se registró correctamente.")
        else:
            messages.error(request, "Escriba una observación antes de guardar.")
        return _redirigir_o_recargar(request, "tareas:detalle", pk=tarea.pk)


class NotificacionesTareaView(ModuloHabilitadoMixin, View):
    """
    Cambios de estado recientes en las tareas del usuario, hechos por otra
    persona (endpoint AJAX para la campana de notificaciones del tablero).
    """

    codigo_modulo = Modulo.MOD03_TAREAS

    def get(self, request):
        notificaciones = [
            {
                "tarea": historial.tarea_id,
                "titulo": historial.tarea.titulo,
                "cliente": historial.tarea.cliente.nombre_razon_social,
                "usuario": historial.usuario.nombre,
                "estado_anterior": historial.estado_anterior,
                "estado_nuevo": historial.estado_nuevo,
                "fecha": historial.fecha_cambio.isoformat(),
                "url": reverse("tareas:detalle", kwargs={"pk": historial.tarea_id}),
            }
            for historial in notificaciones_usuario(request.user)
        ]
        return JsonResponse({"total": len(notificaciones), "notificaciones": notificaciones})
