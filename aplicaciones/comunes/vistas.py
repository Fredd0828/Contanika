"""
Vistas compartidas (pr01): archivos subidos con control de acceso, límite de
peticiones y `robots.txt`.
"""

import mimetypes

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404, HttpResponse
from django.views.generic import View

from aplicaciones.seguridad.models import ConfiguracionDespacho

# Carpetas de `media/` que se pueden pedir por dirección. Las demás
# (documentos, cuentas de cobro, adjuntos) solo se descargan por la vista de
# su módulo, que valida el rol y el cliente.
CARPETA_FOTOS = "fotos/"
CARPETA_FIRMAS = "firmas/"
CARPETA_DESPACHO = "despacho/"


class MediaProtegidaView(LoginRequiredMixin, View):
    """
    Sirve las imágenes subidas (foto de perfil, firma y membrete) solo a
    quien tiene sesión y le corresponden: la foto y la firma, a su dueño o al
    Administrador; el membrete, a cualquier usuario. Lo demás responde 404.
    """

    def get(self, request, ruta):
        if not self._puede_ver(request.user, ruta):
            raise Http404("Archivo no disponible.")
        try:
            existe = default_storage.exists(ruta)
        except SuspiciousFileOperation:
            # Intento de salir de la carpeta de archivos (por ejemplo con «..»).
            raise Http404("Archivo no disponible.") from None
        if not existe:
            raise Http404("Archivo no disponible.")
        tipo, _ = mimetypes.guess_type(ruta)
        respuesta = FileResponse(
            default_storage.open(ruta, "rb"), content_type=tipo or "application/octet-stream"
        )
        # Son archivos privados: que no queden en cachés compartidas.
        respuesta.headers["Cache-Control"] = "private, max-age=300"
        return respuesta

    @staticmethod
    def _puede_ver(usuario, ruta):
        if ruta.startswith(CARPETA_DESPACHO):
            return ConfiguracionDespacho.objects.filter(membrete=ruta).exists()
        if ruta.startswith(CARPETA_FOTOS):
            return usuario.es_administrador or usuario.foto.name == ruta
        if ruta.startswith(CARPETA_FIRMAS):
            return usuario.es_administrador or usuario.firma.name == ruta
        return False


class LimitePeticionesMixin:
    """
    Limita cuántas veces por minuto una misma dirección IP puede pedir la
    vista (`limite_por_minuto`). Protege las rutas públicas de quien prueba
    enlaces o descarga en masa. Al pasarse responde 429.
    """

    limite_por_minuto = 30

    def dispatch(self, request, *args, **kwargs):
        clave = f"limite:{type(self).__name__}:{direccion_ip(request)}"
        if cache.add(clave, 1, timeout=60):
            pedidas = 1
        else:
            try:
                pedidas = cache.incr(clave)
            except ValueError:  # La clave venció entre las dos operaciones.
                cache.add(clave, 1, timeout=60)
                pedidas = 1
        if pedidas > self.limite_por_minuto:
            respuesta = HttpResponse("Demasiadas solicitudes. Intente de nuevo en un minuto.", status=429)
            respuesta.headers["Retry-After"] = "60"
            return respuesta
        return super().dispatch(request, *args, **kwargs)


def direccion_ip(request):
    """IP del visitante. Tras el proxy del servidor, la primera de `X-Forwarded-For`."""
    if settings.CONFIAR_EN_PROXY:
        reenviada = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if reenviada:
            return reenviada.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class RobotsView(View):
    """
    `robots.txt`: pide a los buscadores y rastreadores que no recorran el sistema.

    Solo se les deja leer la página web de inicio (`/`), que es pública y no
    muestra datos del despacho.
    """

    def get(self, request):
        return HttpResponse("User-agent: *\nAllow: /$\nDisallow: /\n", content_type="text/plain")
