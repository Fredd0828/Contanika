"""
Procesadores de contexto del módulo de seguridad.

Construyen el menú lateral con los módulos habilitados para el rol del
usuario y calculan las iniciales que se muestran en el avatar. Al estar
disponibles en todas las plantillas, cualquier página puede dibujar la
barra lateral sin repetir lógica.
"""

from django.urls import NoReverseMatch, reverse

from .menu import ROLES_POR_RUTA, SECCIONES_MENU


def _iniciales(nombre):
    """Toma la primera letra de las dos primeras palabras del nombre."""
    partes = [parte for parte in nombre.split() if parte]
    if not partes:
        return "??"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[1][0]).upper()


def menu_lateral(request):
    """Devuelve las secciones del menú visibles para el usuario autenticado."""
    usuario = getattr(request, "user", None)
    if not usuario or not usuario.is_authenticated:
        return {}

    secciones = []
    for titulo, elementos in SECCIONES_MENU:
        visibles = []
        for etiqueta, nombre_ruta, icono, codigo_modulo in elementos:
            if codigo_modulo and not usuario.tiene_modulo_habilitado(codigo_modulo):
                continue
            roles = ROLES_POR_RUTA.get(nombre_ruta)
            if roles and usuario.rol.nombre_rol not in roles:
                continue
            url = None
            if nombre_ruta:
                try:
                    url = reverse(nombre_ruta)
                except NoReverseMatch:
                    url = None
            if url == "/":
                activo = request.path == "/"
            else:
                activo = bool(url) and request.path.startswith(url)
            visibles.append(
                {
                    "etiqueta": etiqueta,
                    "url": url,
                    "icono": icono,
                    "activo": activo,
                    "disponible": bool(url),
                }
            )
        if visibles:
            secciones.append({"titulo": titulo, "items": visibles})

    return {
        "menu_lateral": secciones,
        "iniciales_usuario": _iniciales(usuario.nombre),
        "nombre_corto": usuario.nombre.split()[0] if usuario.nombre else usuario.correo,
    }
