"""
Configuración base del proyecto Contanika.

Contiene los parámetros comunes a todos los entornos (aplicaciones instaladas,
middleware, plantillas, base de datos, autenticación, seguridad y correo).
Los entornos local y producción heredan de este archivo y solo sobreescriben
lo que cambia entre uno y otro.
"""

from pathlib import Path

from decouple import Csv, config

# Ruta raíz del proyecto (carpeta codigo/), usada para ubicar plantillas y estáticos.
RUTA_BASE = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY", default="clave-solo-para-desarrollo-local")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

# ---------------------------------------------------------------
# Aplicaciones instaladas
# ---------------------------------------------------------------
APLICACIONES_DJANGO = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

APLICACIONES_TERCEROS = [
    "rest_framework",
    "axes",
]

# Las once aplicaciones propias del sistema, en el orden del modelo relacional.
APLICACIONES_PROPIAS = [
    "aplicaciones.comunes",
    "aplicaciones.seguridad",
    "aplicaciones.clientes",
    "aplicaciones.calendario",
    "aplicaciones.tareas",
    "aplicaciones.documentos",
    "aplicaciones.hallazgos",
    "aplicaciones.expediente",
    "aplicaciones.finanzas",
    "aplicaciones.comunicaciones",
    "aplicaciones.reportes",
]

INSTALLED_APPS = APLICACIONES_DJANGO + APLICACIONES_TERCEROS + APLICACIONES_PROPIAS

# ---------------------------------------------------------------
# Middleware (seguridad, sesiones, CSRF, autenticación y bloqueo de intentos)
# ---------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
    "aplicaciones.comunes.middleware.CabecerasSeguridadMiddleware",
    "aplicaciones.comunes.middleware.MonitorConsultasMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [RUTA_BASE / "plantillas"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "aplicaciones.seguridad.context_processors.menu_lateral",
                "aplicaciones.calendario.context_processors.avisos_vencimientos",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------
# Base de datos PostgreSQL (local en desarrollo, Supabase en producción)
# ---------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("BD_NOMBRE", default="contanika_bd"),
        "USER": config("BD_USUARIO", default="contanika"),
        "PASSWORD": config("BD_CLAVE", default="contanika"),
        "HOST": config("BD_HOST", default="127.0.0.1"),
        "PORT": config("BD_PUERTO", default="5432"),
        "CONN_MAX_AGE": 60,
    }
}

# ---------------------------------------------------------------
# Autenticación: modelo de usuario propio y roles del sistema
# ---------------------------------------------------------------
AUTH_USER_MODEL = "seguridad.Usuario"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "seguridad:iniciar_sesion"
LOGIN_REDIRECT_URL = "seguridad:panel"
LOGOUT_REDIRECT_URL = "seguridad:iniciar_sesion"

# ---------------------------------------------------------------
# Internacionalización y zona horaria de Colombia
# ---------------------------------------------------------------
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------
# Archivos estáticos y multimedia
# ---------------------------------------------------------------
STATIC_URL = "estaticos/"
STATICFILES_DIRS = [RUTA_BASE / "estaticos"]
STATIC_ROOT = RUTA_BASE / "estaticos_recolectados"

MEDIA_URL = "media/"
MEDIA_ROOT = RUTA_BASE / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------
# Bloqueo de fuerza bruta en el inicio de sesión (django-axes)
# ---------------------------------------------------------------
AXES_FAILURE_LIMIT = config("AXES_INTENTOS_MAXIMOS", default=5, cast=int)
AXES_COOLOFF_TIME = config("AXES_TIEMPO_BLOQUEO_HORAS", default=1, cast=int)
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address"]
AXES_RESET_ON_SUCCESS = True

# ---------------------------------------------------------------
# Correo electrónico saliente (alertas, cuentas de cobro y recordatorios)
# ---------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("CORREO_HOST", default="")
EMAIL_PORT = config("CORREO_PUERTO", default=587, cast=int)
EMAIL_HOST_USER = config("CORREO_USUARIO", default="")
EMAIL_HOST_PASSWORD = config("CORREO_CLAVE", default="")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = config("CORREO_REMITENTE", default="Contanika <no-responder@contanika.co>")

# Dirección pública del sistema: base de los enlaces que reciben los clientes
# (por ejemplo, el PDF de la cuenta de cobro compartido por WhatsApp). En
# producción debe ser el dominio real; 127.0.0.1 solo sirve en el propio equipo.
URL_SITIO = config("URL_SITIO", default="http://127.0.0.1:8000")

# ---------------------------------------------------------------
# Cifrado de credenciales (Módulo 1)
# ---------------------------------------------------------------
CREDENCIAL_CLAVE_CIFRADO = config("CREDENCIAL_CLAVE_CIFRADO", default="")

# ---------------------------------------------------------------
# Django REST Framework: usado para los endpoints AJAX del sistema
# ---------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    # Límite de peticiones por usuario y por visitante sin sesión (pr01).
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "30/minute", "user": "300/minute"},
}

# ===============================================================
# Endurecimiento de seguridad (pr01), común a todos los entornos.
# Lo que exige HTTPS (redirección, HSTS, cookies seguras) está en produccion.py.
# ===============================================================

# --- Cookies de sesión y CSRF ---
# HttpOnly: JavaScript no puede leer la cookie de sesión. SameSite: el
# navegador no la envía en peticiones que nacen en otro sitio.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
# La sesión se cierra sola tras este tiempo sin uso y al cerrar el navegador.
SESSION_COOKIE_AGE = config("SESION_DURACION_HORAS", default=8, cast=int) * 60 * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# --- Cabeceras de seguridad ---
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Política de seguridad de contenido (la envía CabecerasSeguridadMiddleware).
# 'unsafe-inline' se mantiene porque las plantillas llevan scripts y estilos
# en línea; aun así solo se carga código del propio sitio y de jsDelivr.
_CDN = "https://cdn.jsdelivr.net"
CSP_DIRECTIVAS = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-inline'", _CDN],
    "style-src": ["'self'", "'unsafe-inline'", _CDN, "https://fonts.googleapis.com"],
    "font-src": ["'self'", "data:", _CDN, "https://fonts.gstatic.com"],
    "img-src": ["'self'", "data:", "blob:"],
    "connect-src": ["'self'"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "frame-ancestors": ["'none'"],
    # WhatsApp: «Abrir WhatsApp» envía un formulario que redirige a wa.me.
    "form-action": ["'self'", "https://wa.me", "https://api.whatsapp.com"],
}
# El sistema no usa cámara, micrófono, ubicación ni pagos: se le niegan al navegador.
POLITICA_PERMISOS = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"

# --- Subida de archivos ---
# Tope del cuerpo de una petición sin archivos y del total de campos de un formulario.
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 2000
DATA_UPLOAD_MAX_NUMBER_FILES = 10
# Los archivos subidos quedan sin permiso de ejecución.
FILE_UPLOAD_PERMISSIONS = 0o640
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o750

# --- Panel de administración de Django ---
# En producción conviene publicarlo en una dirección que no sea la habitual
# (RUTA_ADMIN en el .env, terminada en «/»), para que los robots no lo encuentren.
RUTA_ADMIN = config("RUTA_ADMIN", default="admin/")

# --- Límite de peticiones ---
# Tras el proxy del servidor, la IP real del visitante llega en X-Forwarded-For.
CONFIAR_EN_PROXY = config("CONFIAR_EN_PROXY", default=False, cast=bool)

# --- Monitoreo de consultas a la base de datos ---
BD_CONSULTA_LENTA_MS = config("BD_CONSULTA_LENTA_MS", default=500, cast=int)
BD_MAXIMO_CONSULTAS = config("BD_MAXIMO_CONSULTAS", default=150, cast=int)

# --- Registros (carpeta registros/, fuera del repositorio) ---
RUTA_REGISTROS = RUTA_BASE / "registros"
RUTA_REGISTROS.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detallado": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "consola": {"class": "logging.StreamHandler", "formatter": "detallado"},
        "seguridad": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": RUTA_REGISTROS / "seguridad.log",
            "maxBytes": 2 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "detallado",
            "encoding": "utf-8",
            "delay": True,
        },
        "consultas": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": RUTA_REGISTROS / "consultas.log",
            "maxBytes": 2 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "detallado",
            "encoding": "utf-8",
            "delay": True,
        },
    },
    "loggers": {
        # Peticiones sospechosas, CSRF rechazado y hosts no permitidos.
        "django.security": {"handlers": ["seguridad", "consola"], "level": "WARNING", "propagate": False},
        # Respuestas 4xx y 5xx (accesos denegados y errores).
        "django.request": {"handlers": ["seguridad", "consola"], "level": "WARNING", "propagate": False},
        # Intentos fallidos y bloqueos del inicio de sesión.
        "axes": {"handlers": ["seguridad"], "level": "WARNING", "propagate": False},
        # Consultas lentas y peticiones con demasiadas consultas.
        "contanika.consultas": {"handlers": ["consultas", "consola"], "level": "WARNING", "propagate": False},
    },
}
