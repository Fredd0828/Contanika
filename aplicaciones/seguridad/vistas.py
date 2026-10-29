"""
Vistas del módulo 8: inicio de sesión, panel principal, equipo de trabajo,
permisos de módulos por rol, panel de equipo y perfil propio.

Permisos (HU022-HU024, HU050):
- Gestión de usuarios y de módulos por rol: solo el Administrador.
- Panel de trabajo del equipo: Administrador y Contador Senior (solo consulta).
- Perfil propio: cualquier usuario con sesión; no depende de la habilitación
  de módulos, igual que el inicio de sesión (HU050-4).
"""

from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, TemplateView, View

from aplicaciones.comunes.paginacion import PaginacionMixin
from aplicaciones.comunes.vistas import LimitePeticionesMixin

from . import guias, menu, panel, selectores, servicios
from .formularios import (
    CambiarClaveForm,
    FiltroUsuariosForm,
    InicioSesionForm,
    PerfilForm,
    UsuarioCrearForm,
    UsuarioEditarForm,
)
from .models import Modulo, Rol
from .permisos import ModuloHabilitadoMixin, RolRequeridoMixin

Usuario = get_user_model()

ROLES_PANEL_EQUIPO = (Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR)


class PaginaInicioView(LimitePeticionesMixin, TemplateView):
    """
    Página web pública de Contanika: presenta la plataforma y lleva al inicio de sesión.

    No muestra datos del despacho. Quien ya tiene sesión entra directo al sistema.
    """

    template_name = "seguridad/inicio.html"
    limite_por_minuto = 60

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("seguridad:panel")
        respuesta = super().get(request, *args, **kwargs)
        # Única página que puede aparecer en buscadores (el resto lleva «noindex»).
        respuesta.headers["X-Robots-Tag"] = "index, follow"
        return respuesta


class IniciarSesionView(LoginView):
    """Formulario de acceso al sistema (CU001)."""

    template_name = "seguridad/iniciar_sesion.html"
    authentication_form = InicioSesionForm
    redirect_authenticated_user = True


class CerrarSesionView(LogoutView):
    """Cierra la sesión activa y regresa al inicio de sesión."""

    next_page = reverse_lazy("seguridad:iniciar_sesion")


class PanelView(LoginRequiredMixin, TemplateView):
    """
    Panel principal del sistema.

    Tablero gráfico con vencimientos, tareas, finanzas, hallazgos y carga del
    equipo. Cada sección aparece solo si el rol tiene habilitado su módulo
    (RQF031) y con la misma información que el usuario ve dentro del módulo.
    """

    template_name = "seguridad/panel.html"

    def dispatch(self, request, *args, **kwargs):
        # Quien tiene el panel inhabilitado para su rol empieza en su primer módulo.
        if request.user.is_authenticated:
            inicio = menu.ruta_de_inicio(request.user)
            if inicio != menu.RUTA_PANEL:
                return redirect(inicio)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["tablero"] = panel.armar_tablero(self.request.user)
        return contexto


# ---------------------------------------------------------------------------
# Panel de trabajo del equipo (HU023)
# ---------------------------------------------------------------------------


class PanelEquipoView(ModuloHabilitadoMixin, RolRequeridoMixin, TemplateView):
    """Resumen de tareas y vencimientos de cada miembro (Administrador y Senior, solo consulta)."""

    codigo_modulo = Modulo.MOD08_EQUIPO
    roles_permitidos = ROLES_PANEL_EQUIPO
    template_name = "seguridad/equipo/panel.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["resumen"] = selectores.resumen_equipo()
        contexto["limite_pendientes"] = selectores.LIMITE_TAREAS_PENDIENTES
        contexto["es_administrador"] = self.request.user.es_administrador
        return contexto


# ---------------------------------------------------------------------------
# Gestión de usuarios (HU022, solo Administrador)
# ---------------------------------------------------------------------------


class MixinAdministrarEquipo(ModuloHabilitadoMixin, RolRequeridoMixin):
    codigo_modulo = Modulo.MOD08_EQUIPO
    roles_permitidos = (Rol.ADMINISTRADOR,)


def _avisar_correo(request, correo_enviado, usuario):
    if correo_enviado is False:
        messages.warning(
            request,
            f"No se pudo enviar el correo a {usuario.correo}. Entréguele sus datos de acceso por otro medio.",
        )


class ListaUsuariosView(MixinAdministrarEquipo, PaginacionMixin, ListView):
    """Listado del equipo con filtros por nombre, rol y estado."""

    template_name = "seguridad/equipo/usuarios.html"
    context_object_name = "usuarios"

    def get_queryset(self):
        self.formulario_filtro = FiltroUsuariosForm(self.request.GET or None)
        filtros = self.formulario_filtro.cleaned_data if self.formulario_filtro.is_valid() else {}
        return selectores.filtrar_usuarios(
            rol=filtros.get("rol"), estado=filtros.get("estado"), texto=filtros.get("texto")
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["formulario_filtro"] = self.formulario_filtro
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto


class CrearUsuarioView(MixinAdministrarEquipo, View):
    """Alta de un usuario con rol y contraseña temporal; revisa los permisos del rol (HU022-2)."""

    template_name = "seguridad/equipo/usuario_form.html"

    def _contexto(self, formulario):
        return {
            "formulario": formulario,
            "accion": "crear",
            "modulos_por_rol": selectores.modulos_por_rol(),
        }

    def get(self, request):
        return render(request, self.template_name, self._contexto(UsuarioCrearForm()))

    def post(self, request):
        formulario = UsuarioCrearForm(request.POST)
        if formulario.is_valid():
            try:
                usuario, correo_enviado = servicios.crear_usuario(
                    formulario, confirmado=formulario.cleaned_data["confirmar_otro_administrador"]
                )
            except servicios.ErrorEquipo as error:
                formulario.add_error(None, str(error))
            else:
                messages.success(request, f"Se creó el usuario {usuario.nombre}.")
                _avisar_correo(request, correo_enviado, usuario)
                return redirect("seguridad:usuarios")
        return render(request, self.template_name, self._contexto(formulario))


class EditarUsuarioView(MixinAdministrarEquipo, View):
    """Edita datos, correo, rol y contraseña temporal de un usuario."""

    template_name = "seguridad/equipo/usuario_form.html"

    def _contexto(self, formulario, usuario):
        return {
            "formulario": formulario,
            "accion": "editar",
            "usuario_editado": usuario,
            "modulos_por_rol": selectores.modulos_por_rol(),
        }

    def get(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        return render(
            request, self.template_name, self._contexto(UsuarioEditarForm(instance=usuario), usuario)
        )

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        formulario = UsuarioEditarForm(request.POST, instance=usuario)
        if formulario.is_valid():
            try:
                usuario, correo_enviado = servicios.actualizar_usuario(
                    formulario, confirmado=formulario.cleaned_data["confirmar_otro_administrador"]
                )
            except servicios.ErrorEquipo as error:
                formulario.add_error(None, str(error))
            else:
                messages.success(request, f"Se actualizaron los datos de {usuario.nombre}.")
                _avisar_correo(request, correo_enviado, usuario)
                return redirect("seguridad:usuarios")
        usuario.refresh_from_db()
        return render(request, self.template_name, self._contexto(formulario, usuario))


class CambiarEstadoUsuarioView(MixinAdministrarEquipo, View):
    """Activa o inactiva un usuario (POST)."""

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        estado = Usuario.INACTIVO if usuario.estado == Usuario.ACTIVO else Usuario.ACTIVO
        try:
            servicios.cambiar_estado_usuario(
                usuario, estado, request.user, confirmado=request.POST.get("confirmar") == "1"
            )
        except servicios.ErrorEquipo as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"{usuario.nombre} quedó {estado.lower()}.")
        return redirect("seguridad:usuarios")


class EliminarUsuarioView(MixinAdministrarEquipo, View):
    """Elimina un usuario sin historial (POST); si tiene historial se sugiere inactivarlo."""

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        nombre = usuario.nombre
        try:
            servicios.eliminar_usuario(usuario, request.user)
        except servicios.ErrorEquipo as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"Se eliminó el usuario {nombre}.")
        return redirect("seguridad:usuarios")


# ---------------------------------------------------------------------------
# Módulos por rol (HU050, solo Administrador)
# ---------------------------------------------------------------------------


class PermisosModulosView(MixinAdministrarEquipo, View):
    """Interruptores de habilitación de cada módulo por rol."""

    template_name = "seguridad/equipo/permisos.html"

    def get(self, request):
        roles, filas = selectores.matriz_permisos()
        return render(request, self.template_name, {"roles": roles, "filas": filas})

    def post(self, request):
        habilitados = set()
        for clave in request.POST:
            if clave.startswith("permiso_"):
                try:
                    _, id_rol, id_modulo = clave.split("_")
                    habilitados.add((int(id_rol), int(id_modulo)))
                except ValueError:
                    continue
        servicios.guardar_permisos_modulos(habilitados)
        messages.success(request, "Se guardó la configuración de módulos por rol.")
        return redirect("seguridad:permisos")


# ---------------------------------------------------------------------------
# Perfil propio (HU024, cualquier usuario)
# ---------------------------------------------------------------------------


PLANTILLA_PERFIL = "seguridad/perfil.html"


def _es_firmante(usuario):
    """Quienes firman documentos del Módulo 4 cargan en su perfil la firma y la tarjeta profesional."""
    return usuario.rol.nombre_rol in (Rol.ADMINISTRADOR, Rol.CONTADOR_SENIOR)


class PerfilView(LoginRequiredMixin, View):
    """Datos propios del usuario; el correo y el rol solo los cambia el Administrador."""

    def _render(self, request, formulario):
        contexto = {"formulario": formulario, "formulario_clave": CambiarClaveForm(request.user)}
        return render(request, PLANTILLA_PERFIL, contexto)

    def get(self, request):
        return self._render(request, PerfilForm(instance=request.user, firmante=_es_firmante(request.user)))

    def post(self, request):
        formulario = PerfilForm(
            request.POST, request.FILES, instance=request.user, firmante=_es_firmante(request.user)
        )
        if formulario.is_valid():
            servicios.actualizar_perfil(formulario)
            messages.success(request, "Su perfil se actualizó correctamente.")
            return redirect("seguridad:perfil")
        request.user.refresh_from_db()
        return self._render(request, formulario)


class CambiarClaveView(LoginRequiredMixin, View):
    """Cambio de contraseña propia: exige la actual y conserva la sesión abierta."""

    def post(self, request):
        formulario_clave = CambiarClaveForm(request.user, request.POST)
        if formulario_clave.is_valid():
            usuario = formulario_clave.save()
            update_session_auth_hash(request, usuario)
            messages.success(request, "Su contraseña se cambió correctamente.")
            return redirect("seguridad:perfil")
        contexto = {
            "formulario": PerfilForm(instance=request.user, firmante=_es_firmante(request.user)),
            "formulario_clave": formulario_clave,
        }
        return render(request, PLANTILLA_PERFIL, contexto)


# ---------------------------------------------------------------------------
# Ayuda (HU053, cualquier usuario)
# ---------------------------------------------------------------------------


class AyudaView(LoginRequiredMixin, TemplateView):
    """
    Guías paso a paso de los procesos, guía rápida de los módulos, preguntas
    frecuentes y contacto de soporte del despacho.
    """

    template_name = "seguridad/ayuda.html"

    def get_context_data(self, **kwargs):
        from .models import ConfiguracionDespacho

        contexto = super().get_context_data(**kwargs)
        contexto["despacho"] = ConfiguracionDespacho.objects.first()
        contexto["grupos_guias"] = guias.guias_por_grupo(self.request.user)
        return contexto


class GuiaAyudaView(LoginRequiredMixin, TemplateView):
    """
    Una guía paso a paso. Solo abre las guías de procesos que el usuario puede
    hacer (su rol y sus módulos habilitados); las demás responden 403.
    """

    template_name = "seguridad/guia.html"

    def get_context_data(self, **kwargs):
        guia = guias.POR_SLUG.get(kwargs["slug"])
        if guia is None:
            raise Http404("La guía no existe.")
        if not guias.es_visible(guia, self.request.user):
            raise PermissionDenied("Esta guía no aplica para su rol.")
        contexto = super().get_context_data(**kwargs)
        contexto["guia"] = guia
        contexto["url_pantalla"] = reverse(guia.ruta) if guia.ruta else None
        contexto["relacionadas"] = [
            guias.POR_SLUG[slug]
            for slug in guia.relacionadas
            if guias.es_visible(guias.POR_SLUG[slug], self.request.user)
        ]
        return contexto
