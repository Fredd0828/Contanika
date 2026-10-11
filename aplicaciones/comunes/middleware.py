"""
Middleware de seguridad transversal (pr01).

- `CabecerasSeguridadMiddleware`: política de seguridad de contenido (CSP),
  política de permisos del navegador y aviso a los buscadores de no indexar.
- `MonitorConsultasMiddleware`: registra las consultas lentas a la base de
  datos y las peticiones que hacen demasiadas consultas.
"""

import logging
import time

from django.conf import settings
from django.db import connection

registro_consultas = logging.getLogger("contanika.consultas")


class CabecerasSeguridadMiddleware:
    """
    Agrega las cabeceras de seguridad que Django no trae de serie.

    La CSP limita de dónde puede cargar el navegador scripts, estilos, fuentes
    e imágenes (solo el propio sitio y los CDN que usa la plataforma), impide
    que la página se muestre dentro de un marco ajeno y a dónde se envían los
    formularios. Así, aunque se colara contenido malicioso, no podría traer
    código de otro servidor ni enviar datos fuera.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.csp = "; ".join(
            f"{directiva} {' '.join(fuentes)}" for directiva, fuentes in settings.CSP_DIRECTIVAS.items()
        )

    def __call__(self, request):
        respuesta = self.get_response(request)
        respuesta.headers.setdefault("Content-Security-Policy", self.csp)
        respuesta.headers.setdefault("Permissions-Policy", settings.POLITICA_PERMISOS)
        # Es un sistema interno: ninguna de sus páginas debe aparecer en buscadores.
        respuesta.headers.setdefault("X-Robots-Tag", "noindex, nofollow")
        return respuesta


class MonitorConsultasMiddleware:
    """
    Vigila las consultas de cada petición.

    Deja en el registro `contanika.consultas` cada consulta que tarde más de
    `BD_CONSULTA_LENTA_MS` y cada petición que supere `BD_MAXIMO_CONSULTAS`
    consultas (señal de una pantalla que consulta fila por fila). No guarda
    los parámetros de la consulta, para no dejar datos de clientes en el
    registro.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        medidor = _MedidorConsultas(request)
        with connection.execute_wrapper(medidor):
            respuesta = self.get_response(request)
        if medidor.total > settings.BD_MAXIMO_CONSULTAS:
            registro_consultas.warning(
                "Petición con %s consultas (%.0f ms en base de datos): %s %s",
                medidor.total,
                medidor.milisegundos,
                request.method,
                request.path,
            )
        return respuesta


class _MedidorConsultas:
    """Envoltorio de `connection.execute_wrapper`: cuenta y cronometra cada consulta."""

    def __init__(self, request):
        self.request = request
        self.total = 0
        self.milisegundos = 0.0

    def __call__(self, ejecutar, sql, parametros, varias, contexto):
        inicio = time.monotonic()
        try:
            return ejecutar(sql, parametros, varias, contexto)
        finally:
            duracion = (time.monotonic() - inicio) * 1000
            self.total += 1
            self.milisegundos += duracion
            if duracion >= settings.BD_CONSULTA_LENTA_MS:
                registro_consultas.warning(
                    "Consulta lenta (%.0f ms) en %s %s: %s",
                    duracion,
                    self.request.method,
                    self.request.path,
                    " ".join(str(sql).split())[:300],
                )
