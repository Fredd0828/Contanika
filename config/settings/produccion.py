"""
Configuración del entorno de producción sobre Supabase.

Activa todas las protecciones de seguridad exigidas por el RQNF004 y exige
que los valores sensibles lleguen por variables de entorno.
"""

from decouple import Csv, config

from .base import *  # noqa: F401,F403
from .base import DATABASES

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

# La base de datos de producción es el proyecto de Supabase (PostgreSQL 15).
DATABASES["default"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": config("BD_NOMBRE", default="postgres"),
    "USER": config("BD_USUARIO", default="postgres"),
    "PASSWORD": config("BD_CLAVE"),
    "HOST": config("BD_HOST"),
    "PORT": config("BD_PUERTO", default="5432"),
    "CONN_MAX_AGE": 600,
    "OPTIONS": {"sslmode": config("BD_SSL_MODE", default="require")},
}

# ---------------------------------------------------------------
# Endurecimiento de seguridad para producción
# ---------------------------------------------------------------
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_TRUSTED_ORIGINS = config("CSRF_ORIGENES_CONFIABLES", default="", cast=Csv())

# Almacenamiento de estáticos comprimido y con caché larga (Django 5.x).
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
