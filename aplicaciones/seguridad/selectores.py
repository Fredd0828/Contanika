"""Consultas reutilizables del módulo 8: equipo de trabajo, roles y permisos."""

from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from .models import Modulo, PermisoRolModulo, Rol, Usuario

# Un miembro con más pendientes que este límite se marca con alerta (HU023-5).
LIMITE_TAREAS_PENDIENTES = 10
DIAS_VENCIMIENTOS_PROXIMOS = 7


def filtrar_usuarios(rol=None, estado=None, texto=None):
    """Usuarios del equipo con los filtros desplegables del listado."""
    consulta = Usuario.objects.select_related("rol")
    if rol:
        consulta = consulta.filter(rol=rol)
    if estado:
        consulta = consulta.filter(estado=estado)
    if texto:
        consulta = consulta.filter(Q(nombre__icontains=texto) | Q(correo__icontains=texto))
    return consulta


def matriz_permisos():
    """
    Filas de la configuración de módulos por rol: cada módulo con el estado
    de habilitación para cada rol (sin fila guardada se considera habilitado).
    """
    from .servicios import es_permiso_fijo

    roles = list(Rol.objects.all())
    guardados = {(p.rol_id, p.modulo_id): p.habilitado for p in PermisoRolModulo.objects.all()}
    filas = []
    for modulo in Modulo.objects.all():
        celdas = [
            {
                "rol": rol,
                "habilitado": guardados.get((rol.pk, modulo.pk), True),
                "fijo": es_permiso_fijo(rol, modulo),
                "nombre_campo": f"permiso_{rol.pk}_{modulo.pk}",
            }
            for rol in roles
        ]
        filas.append({"modulo": modulo, "celdas": celdas})
    return roles, filas


def modulos_por_rol():
    """Módulos habilitados de cada rol, para revisarlos al crear un usuario (HU022-2)."""
    roles, filas = matriz_permisos()
    return {
        rol.pk: [fila["modulo"].nombre_modulo for fila in filas if fila["celdas"][indice]["habilitado"]]
        for indice, rol in enumerate(roles)
    }


def resumen_equipo(hoy=None):
    """
    Panel de trabajo del equipo (HU023, RQF029). Para cada miembro activo:
    tareas activas, porcentaje de completado de las tareas que vencen en el
    mes, vencimientos de los próximos 7 días y alerta por exceso de pendientes.
    """
    from aplicaciones.calendario.models import Vencimiento
    from aplicaciones.tareas.models import Tarea

    hoy = hoy or timezone.localdate()
    # Tareas que vencen en el mes en curso: base del porcentaje de completado.
    del_mes = Q(
        tareas_asignadas__fecha_vencimiento__year=hoy.year,
        tareas_asignadas__fecha_vencimiento__month=hoy.month,
    )
    miembros = (
        Usuario.objects.filter(estado=Usuario.ACTIVO)
        .select_related("rol")
        .annotate(
            tareas_activas=Count("tareas_asignadas", filter=~Q(tareas_asignadas__estado=Tarea.TERMINADO)),
            tareas_mes=Count("tareas_asignadas", filter=del_mes),
            terminadas_mes=Count(
                "tareas_asignadas", filter=del_mes & Q(tareas_asignadas__estado=Tarea.TERMINADO)
            ),
        )
        .order_by("-tareas_activas", "nombre")
    )
    limite = hoy + timedelta(days=DIAS_VENCIMIENTOS_PROXIMOS)
    proximos = (
        Vencimiento.objects.filter(fecha_vencimiento__range=(hoy, limite), responsable__isnull=False)
        .exclude(estado_presentacion=Vencimiento.PRESENTADA)
        .select_related("cliente")
        .order_by("fecha_vencimiento")
    )
    por_responsable = {}
    for vencimiento in proximos:
        por_responsable.setdefault(vencimiento.responsable_id, []).append(vencimiento)

    resumen = []
    for miembro in miembros:
        porcentaje = round(100 * miembro.terminadas_mes / miembro.tareas_mes) if miembro.tareas_mes else None
        resumen.append(
            {
                "usuario": miembro,
                "tareas_activas": miembro.tareas_activas,
                "tareas_mes": miembro.tareas_mes,
                "terminadas_mes": miembro.terminadas_mes,
                "porcentaje_mes": porcentaje,
                "vencimientos": por_responsable.get(miembro.pk, []),
                "alerta": miembro.tareas_activas > LIMITE_TAREAS_PENDIENTES,
            }
        )
    return resumen
