"""
Procesador de contexto del módulo 2: avisos de vencimientos próximos.

Alimenta la campana de la barra superior, disponible en todas las páginas, con
las alertas del Calendario que le corresponden al usuario (HU040-2 y 5).
"""

from aplicaciones.seguridad.models import Modulo

from . import selectores
from .servicios import enlace_whatsapp_alerta

# Cantidad máxima de avisos que se dibujan en el desplegable de la campana.
MAXIMO_AVISOS_VISIBLES = 8


def avisos_vencimientos(request):
    """Avisos de vencimientos próximos del usuario autenticado, si tiene el Calendario habilitado."""
    usuario = getattr(request, "user", None)
    if not usuario or not usuario.is_authenticated:
        return {}
    if not usuario.tiene_modulo_habilitado(Modulo.MOD02_CALENDARIO):
        return {}
    avisos = selectores.avisos_para_usuario(usuario)
    for aviso in avisos:
        aviso["enlace_whatsapp"] = (
            enlace_whatsapp_alerta(aviso["vencimiento"], usuario) if aviso["whatsapp"] else None
        )
    return {
        "avisos_vencimientos": avisos[:MAXIMO_AVISOS_VISIBLES],
        "total_avisos_vencimientos": len(avisos),
    }
