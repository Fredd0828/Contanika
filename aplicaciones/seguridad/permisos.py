"""
Reglas de autorización por módulo, rol y reporte.

Estos mixins se usan en las vistas del sistema para garantizar que cada rol
acceda únicamente a los módulos que el Administrador tiene habilitados
(RQF031) y a las acciones propias de su perfil (RQF009).
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class ModuloHabilitadoMixin(LoginRequiredMixin):
    """
    Exige que el usuario tenga habilitado el módulo indicado en `codigo_modulo`.

    Un módulo inhabilitado para el rol bloquea el acceso directo por URL,
    aunque no elimina los datos ya registrados (RQF031).
    """

    codigo_modulo = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.codigo_modulo and not request.user.tiene_modulo_habilitado(self.codigo_modulo):
            raise PermissionDenied("El módulo no está habilitado para su rol.")
        return super().dispatch(request, *args, **kwargs)


class RolRequeridoMixin(LoginRequiredMixin):
    """Restringe la vista a los roles indicados en `roles_permitidos`."""

    roles_permitidos = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.roles_permitidos and request.user.rol.nombre_rol not in self.roles_permitidos:
            raise PermissionDenied("Su rol no tiene permiso para realizar esta acción.")
        return super().dispatch(request, *args, **kwargs)


class ReporteHabilitadoMixin(LoginRequiredMixin):
    """
    Exige que el rol del usuario tenga habilitado el reporte indicado.

    El Administrador configura esta visibilidad reporte por reporte dentro
    del módulo 10 (RQF015).
    """

    nombre_reporte = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.nombre_reporte and not request.user.puede_ver_reporte(self.nombre_reporte):
            raise PermissionDenied("El reporte no está habilitado para su rol.")
        return super().dispatch(request, *args, **kwargs)
