"""
Configuración del entorno de producción sobre Supabase.

Activa todas las protecciones de seguridad exigidas por el RQNF004 y exige
que los valores sensibles lleguen por variables de entorno: sin ellos, o con
los de desarrollo, el sistema no arranca (pr01).
"""

from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import REST_FRAMEWORK

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

# ---------------------------------------------------------------
# Secretos obligatorios: sin valor por defecto y sin los de desarrollo
# ---------------------------------------------------------------
CLAVES_DE_DESARROLLO = ("clave-solo-para-desarrollo-local", "clave-secreta-de-desarrollo-solo-local")

SECRET_KEY = config("SECRET_KEY")
if SECRET_KEY in CLAVES_DE_DESARROLLO or len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5:
    raise ImproperlyConfigured(
        "SECRET_KEY de producción no válida: genere una larga y aleatoria con "
        '`python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"` '
        "y guárdela en el .env del servidor."
    )

CREDENCIAL_CLAVE_CIFRADO = config("CREDENCIAL_CLAVE_CIFRADO")
if not CREDENCIAL_CLAVE_CIFRADO:
    raise ImproperlyConfigured(
        "Falta CREDENCIAL_CLAVE_CIFRADO: sin ella no se pueden cifrar las credenciales."
    )

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("Falta ALLOWED_HOSTS: indique el dominio del sistema.")

# ---------------------------------------------------------------
# Base de datos: proyecto de Supabase (PostgreSQL), siempre cifrada
# ---------------------------------------------------------------
# La aplicación entra con un usuario propio de privilegios mínimos (ver
# scripts/bd/03_rol_aplicacion.sql), nunca con el superusuario `postgres`.
BD_USUARIO = config("BD_USUARIO")
# Por el pooler de Supabase el usuario llega como `rol.referencia-del-proyecto`.
if BD_USUARIO.split(".")[0] == "postgres":
    raise ImproperlyConfigured(
        "BD_USUARIO no puede ser `postgres` en producción: use el rol de la aplicación "
        "(scripts/bd/03_rol_aplicacion.sql)."
    )

# Se define un diccionario nuevo (no se modifica el de base.py).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("BD_NOMBRE", default="postgres"),
        "USER": BD_USUARIO,
        "PASSWORD": config("BD_CLAVE"),
        "HOST": config("BD_HOST"),
        "PORT": config("BD_PUERTO", default="5432"),
        "CONN_MAX_AGE": 600,
        "OPTIONS": {"sslmode": config("BD_SSL_MODE", default="require")},
    }
}

# ---------------------------------------------------------------
# HTTPS obligatorio
# ---------------------------------------------------------------
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CONFIAR_EN_PROXY = True

# Cookies solo por HTTPS. El prefijo __Host- las ata a este dominio exacto.
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "__Host-sesion"
CSRF_COOKIE_NAME = "__Host-csrf"

CSRF_TRUSTED_ORIGINS = config("CSRF_ORIGENES_CONFIABLES", default="", cast=Csv())

# Las respuestas de la API solo salen como JSON (sin la interfaz navegable).
REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"]}

# Almacenamiento de estáticos comprimido y con caché larga (Django 5.x).
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
