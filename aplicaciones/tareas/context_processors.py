"""
Procesador de contexto del módulo 3: cambios recientes en mis tareas.

Alimenta la campana de la barra superior, en todas las páginas, con los
cambios de estado que otra persona hizo en las tareas del usuario (decisión
del usuario, 18-nov-2026; antes solo se veían dentro del tablero).
"""

from aplicaciones.seguridad.models import Modulo

from .selectores import notificaciones_usuario

# Cantidad máxima de cambios que se dibujan en el desplegable de la campana.
MAXIMO_AVISOS_VISIBLES = 6


def avisos_tareas(request):
    """
    Cambios recientes en las tareas del usuario, si tiene el tablero habilitado.

    `total_avisos_tareas` siempre es un número para el usuario con sesión, para
    poder sumarlo en la campana aunque el módulo esté apagado.
    """
    usuario = getattr(request, "user", None)
    if not usuario or not usuario.is_authenticated:
        return {}
    if not usuario.tiene_modulo_habilitado(Modulo.MOD03_TAREAS):
        return {"total_avisos_tareas": 0}
    avisos = list(notificaciones_usuario(usuario))
    return {
        "avisos_tareas": avisos[:MAXIMO_AVISOS_VISIBLES],
        "total_avisos_tareas": len(avisos),
    }
