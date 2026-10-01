"""Consultas reutilizables del módulo 10: reportes y análisis."""

from aplicaciones.seguridad.models import Rol

from .definiciones import REPORTES
from .models import DescargaReporte, PermisoReporteRol, Reporte


def puede_ver(usuario, definicion):
    """El Administrador ve todos los reportes; los demás roles, los que tengan habilitados."""
    return usuario.es_administrador or usuario.puede_ver_reporte(definicion.nombre)


def reportes_visibles(usuario):
    """Reportes que aparecen en la vista del usuario (un reporte oculto no se muestra)."""
    return [definicion for definicion in REPORTES if puede_ver(usuario, definicion)]


def matriz_visibilidad():
    """Filas reporte × rol para la configuración (sin fila guardada se considera visible)."""
    roles = list(Rol.objects.all())
    guardados = {(p.reporte_id, p.rol_id): p.habilitado for p in PermisoReporteRol.objects.all()}
    filas = []
    for reporte in Reporte.objects.all():
        filas.append(
            {
                "reporte": reporte,
                "celdas": [
                    {
                        "rol": rol,
                        "habilitado": guardados.get((reporte.pk, rol.pk), True),
                        "fijo": rol.nombre_rol == Rol.ADMINISTRADOR,
                        "nombre_campo": f"visible_{reporte.pk}_{rol.pk}",
                    }
                    for rol in roles
                ],
            }
        )
    return roles, filas


def descargas(reporte=None, usuario=None, desde=None, hasta=None):
    """Historial de descargas de reportes, más recientes primero."""
    consulta = DescargaReporte.objects.select_related("reporte", "usuario")
    if reporte:
        consulta = consulta.filter(reporte=reporte)
    if usuario:
        consulta = consulta.filter(usuario=usuario)
    if desde:
        consulta = consulta.filter(fecha_hora__date__gte=desde)
    if hasta:
        consulta = consulta.filter(fecha_hora__date__lte=hasta)
    return consulta
