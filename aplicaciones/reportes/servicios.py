"""Operaciones de escritura del módulo 10: reportes y análisis."""

from django.db import transaction

from aplicaciones.seguridad.models import Rol

from .models import DescargaReporte, PermisoReporteRol, Reporte


def registrar_descarga(nombre_reporte, usuario, formato, filtros_texto):
    """Deja constancia de quién descargó qué reporte, cuándo y con qué filtros (HU028-5)."""
    reporte, _ = Reporte.objects.get_or_create(nombre_reporte=nombre_reporte, defaults={"modulo_origen": ""})
    return DescargaReporte.objects.create(
        reporte=reporte, usuario=usuario, formato=formato, filtros=filtros_texto[:2000]
    )


@transaction.atomic
def guardar_visibilidad(habilitados):
    """
    Guarda qué roles ven cada reporte. `habilitados` es el conjunto de pares
    (id_reporte, id_rol) marcados. El Administrador ve siempre todos los
    reportes, porque es quien configura la visibilidad.
    """
    for reporte in Reporte.objects.all():
        for rol in Rol.objects.all():
            habilitado = rol.nombre_rol == Rol.ADMINISTRADOR or (reporte.pk, rol.pk) in habilitados
            PermisoReporteRol.objects.update_or_create(
                reporte=reporte, rol=rol, defaults={"habilitado": habilitado}
            )
