#!/usr/bin/env bash
# ============================================================
# Contanika - Instalación en un VPS con Ubuntu 24.04 (una sola vez)
#
# Deja el sistema funcionando en https://SU-DOMINIO con:
#   - PostgreSQL en el mismo servidor, con los roles de privilegios
#     mínimos (scripts/bd/03) y RLS (scripts/bd/04).
#   - gunicorn como servicio (systemd) detrás de nginx.
#   - Certificado HTTPS gratis de Let's Encrypt (certbot), renovación sola.
#   - Cortafuegos: solo SSH, HTTP y HTTPS.
#   - Tareas automáticas (cron) y respaldo diario de la base y los archivos.
#   - Un despacho nuevo y vacío: solo el Administrador, que recibe por
#     correo el enlace para crear su contraseña.
#
# Uso, como root en el servidor:
#   curl -fsSLO https://raw.githubusercontent.com/Fredd0828/Contanika/main/despliegue/instalar_vps.sh
#   sudo bash instalar_vps.sh
#
# Hace las preguntas al empezar. Los secretos (claves de la base, SECRET_KEY,
# clave de cifrado) se generan solos y nunca se muestran: quedan en
# /srv/contanika/codigo/.env y /root/contanika-secretos.env.
# Guía completa: documentacion/DESPLIEGUE_VPS.md
# ============================================================
set -euo pipefail

REPO="${REPO:-https://github.com/Fredd0828/Contanika.git}"
RAMA="${RAMA:-main}"
USUARIO=contanika
BASE=/srv/contanika
CODIGO=$BASE/codigo
PYTHON=$CODIGO/.venv/bin/python
SECRETOS=/root/contanika-secretos.env
BD=contanika_bd
PUERTO_APP=8001

paso() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
aviso() { printf '\033[1;33m[!] %s\033[0m\n' "$*"; }
falla() { printf '\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }
aleatorio() { python3 -c "import secrets; print(secrets.token_urlsafe($1))"; }
como_app() { sudo -u "$USUARIO" -H "$@"; }
gestionar() { (cd "$CODIGO" && como_app "$PYTHON" gestionar.py "$@"); }
sql() { sudo -u postgres env PGOPTIONS="-c client_min_messages=warning" psql -v ON_ERROR_STOP=1 -q "$@"; }

preguntar() { # variable, texto, valor por defecto
    local var=$1 texto=$2 defecto=${3:-} valor
    if [[ -z "${!var:-}" ]]; then
        read -rp "$texto${defecto:+ [$defecto]}: " valor
        printf -v "$var" '%s' "${valor:-$defecto}"
    fi
    [[ -n "${!var}" ]] || falla "Falta: $texto"
}

preguntar_secreto() { # variable, texto
    local var=$1 texto=$2 valor
    if [[ -z "${!var:-}" ]]; then
        read -rsp "$texto (no se muestra): " valor
        echo
        printf -v "$var" '%s' "${valor// /}"
    fi
    [[ -n "${!var}" ]] || falla "Falta: $texto"
}

# ------------------------------------------------------------
# 0. Comprobaciones y preguntas
# ------------------------------------------------------------
[[ $EUID -eq 0 ]] || falla "Ejecútelo como root: sudo bash instalar_vps.sh"
# shellcheck disable=SC1091
. /etc/os-release
[[ "$ID" == "ubuntu" ]] || falla "Este script está hecho para Ubuntu 24.04 (encontrado: $PRETTY_NAME)."
[[ ! -d "$CODIGO" ]] || falla "Contanika ya está instalado en $CODIGO. Para actualizar use: sudo bash $CODIGO/despliegue/actualizar.sh"

# Carpeta de trabajo que el usuario contanika también puede leer.
cd /tmp
echo "Instalación de Contanika en este servidor."
echo "Responda las preguntas; lo que va entre corchetes es el valor por defecto."
echo
preguntar DOMINIO "Dirección del sistema, sin https:// (ej. contanika.duckdns.org)"
DOMINIO=${DOMINIO#https://}
DOMINIO=${DOMINIO#http://}
DOMINIO=${DOMINIO%%/*}
preguntar CORREO_AVISOS "Correo para los avisos del certificado HTTPS (Let's Encrypt)"
preguntar NOMBRE_DESPACHO "Nombre del despacho"
preguntar CIUDAD_DESPACHO "Ciudad del despacho" "Bogotá D.C."
preguntar NOMBRE_ADMIN "Nombre del Administrador"
preguntar CORREO_ADMIN "Correo del Administrador (ahí le llega el enlace de acceso)"
preguntar CORREO_USUARIO "Cuenta de Gmail que envía los correos"
preguntar_secreto CORREO_CLAVE "Contraseña de aplicación de esa cuenta (16 letras)"

IP_SERVIDOR=$(hostname -I | awk '{print $1}')
IP_DOMINIO=$(getent ahostsv4 "$DOMINIO" | awk 'NR==1 {print $1}' || true)
if [[ -z "$IP_DOMINIO" ]]; then
    falla "El dominio $DOMINIO no apunta a ninguna IP. Configúrelo (por ejemplo en duckdns.org) con la IP de este servidor y vuelva a intentar."
fi
if ! hostname -I | tr ' ' '\n' | grep -qx "$IP_DOMINIO"; then
    aviso "$DOMINIO apunta a $IP_DOMINIO, pero este servidor tiene $IP_SERVIDOR."
    aviso "Si no coinciden, el certificado HTTPS va a fallar."
    read -rp "¿Continuar de todos modos? (s/N): " seguir
    [[ "$seguir" =~ ^[sS]$ ]] || exit 1
fi

# ------------------------------------------------------------
# 1. Paquetes del sistema
# ------------------------------------------------------------
paso "1/11 Instalando paquetes del sistema"
export DEBIAN_FRONTEND=noninteractive
# Ubuntu 24.04 pregunta qué servicios reiniciar tras actualizar: que lo haga solo.
export NEEDRESTART_MODE=a
apt-get update -q
apt-get upgrade -yq
apt-get install -yq python3-venv python3-dev build-essential git postgresql nginx \
    certbot python3-certbot-nginx ufw cron curl unattended-upgrades
systemctl enable --now postgresql nginx cron

# Memoria de intercambio en servidores pequeños, para que pip y los PDF no se queden sin RAM.
if [[ -z "$(swapon --show)" ]] && (( $(free -m | awk '/^Mem:/ {print $2}') < 3000 )); then
    paso "Creando 2 GB de memoria de intercambio (swap)"
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile >/dev/null
    swapon /swapfile
    grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# ------------------------------------------------------------
# 2. Cortafuegos: solo SSH, HTTP y HTTPS
# ------------------------------------------------------------
paso "2/11 Cortafuegos"
ufw allow OpenSSH >/dev/null
ufw allow 'Nginx Full' >/dev/null
ufw --force enable >/dev/null
ufw status | sed -n '1,8p'

# ------------------------------------------------------------
# 3. Usuario del sistema y código
# ------------------------------------------------------------
paso "3/11 Descargando Contanika ($RAMA)"
id "$USUARIO" &>/dev/null || useradd --system --create-home --home-dir "$BASE" --shell /bin/bash "$USUARIO"
chmod 750 "$BASE"
como_app git clone --quiet --branch "$RAMA" "$REPO" "$CODIGO"
como_app mkdir -p "$CODIGO/media" "$CODIGO/registros"
como_app chmod 750 "$CODIGO/media" "$CODIGO/registros"

paso "4/11 Instalando las librerías de Python"
como_app python3 -m venv "$CODIGO/.venv"
como_app "$CODIGO/.venv/bin/pip" install --quiet --upgrade pip
como_app "$CODIGO/.venv/bin/pip" install --quiet -r "$CODIGO/requirements.txt"

# ------------------------------------------------------------
# 5. Base de datos con roles de privilegios mínimos
# ------------------------------------------------------------
paso "5/11 Creando la base de datos"
CLAVE_DUENO=$(aleatorio 32)
CLAVE_APP=$(aleatorio 32)
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$BD'" | grep -q 1; then
    sql -c "CREATE DATABASE $BD ENCODING 'UTF8' TEMPLATE template0"
fi
# Los scripts van por la entrada estándar: el usuario postgres no puede leer
# /srv/contanika, y así las claves no quedan escritas en ningún archivo.
sed -e "s/CAMBIE_ESTA_CLAVE_DEL_DUENO/$CLAVE_DUENO/" \
    -e "s/CAMBIE_ESTA_CLAVE_DE_LA_APLICACION/$CLAVE_APP/" \
    "$CODIGO/scripts/bd/03_rol_aplicacion.sql" | sql -d "$BD"

# ------------------------------------------------------------
# 6. Archivo .env (secretos generados aquí, nunca se muestran)
# ------------------------------------------------------------
paso "6/11 Generando la configuración (.env)"
SECRET_KEY=$(aleatorio 50)
CLAVE_CIFRADO=$("$PYTHON" -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
RUTA_ADMIN="gestion-$(python3 -c 'import secrets; print(secrets.token_hex(6))')/"
(
    umask 077
    cat > "$CODIGO/.env" <<EOF
# Contanika - producción. Generado por despliegue/instalar_vps.sh el $(date +%F).
# No se sube al repositorio ni se comparte.
ENTORNO=produccion
DEBUG=False
SECRET_KEY=$SECRET_KEY
CREDENCIAL_CLAVE_CIFRADO=$CLAVE_CIFRADO
ALLOWED_HOSTS=$DOMINIO
CSRF_ORIGENES_CONFIABLES=https://$DOMINIO
URL_SITIO=https://$DOMINIO
RUTA_ADMIN=$RUTA_ADMIN

BD_NOMBRE=$BD
BD_USUARIO=contanika_app
BD_CLAVE=$CLAVE_APP
BD_HOST=127.0.0.1
BD_PUERTO=5432
# La base está en este mismo servidor y no sale a internet.
BD_SSL_MODE=disable

CORREO_HOST=smtp.gmail.com
CORREO_PUERTO=587
CORREO_USUARIO=$CORREO_USUARIO
CORREO_CLAVE=$CORREO_CLAVE
CORREO_REMITENTE=Contanika <$CORREO_USUARIO>

SESION_DURACION_HORAS=8
AXES_INTENTOS_MAXIMOS=5
AXES_TIEMPO_BLOQUEO_MINUTOS=15
EOF
    cat > "$SECRETOS" <<EOF
# Solo para despliegue/actualizar.sh: el dueño de las tablas aplica las migraciones.
BD_CLAVE_DUENO=$CLAVE_DUENO
EOF
)
chown "$USUARIO:$USUARIO" "$CODIGO/.env"
chmod 600 "$CODIGO/.env" "$SECRETOS"

# ------------------------------------------------------------
# 7. Tablas, privilegios y RLS
# ------------------------------------------------------------
paso "7/11 Creando las tablas"
(cd "$CODIGO" && como_app env BD_USUARIO=contanika_dueno BD_CLAVE="$CLAVE_DUENO" \
    "$PYTHON" gestionar.py migrate --noinput)
# Con las tablas ya creadas: privilegios de la aplicación y seguridad por fila.
sql -d "$BD" < "$CODIGO/scripts/bd/03_rol_aplicacion.sql"
sql -d "$BD" < "$CODIGO/scripts/bd/04_activar_rls.sql" >/dev/null
gestionar collectstatic --noinput -v 0

# ------------------------------------------------------------
# 8. gunicorn como servicio
# ------------------------------------------------------------
paso "8/11 Servicio de la aplicación (gunicorn)"
NUCLEOS=$(nproc)
TRABAJADORES=$(( NUCLEOS * 2 + 1 ))
if (( TRABAJADORES > 3 )); then TRABAJADORES=3; fi
sed -e "s#__CODIGO__#$CODIGO#g" -e "s#__USUARIO__#$USUARIO#g" \
    -e "s#__PUERTO__#$PUERTO_APP#g" -e "s#__TRABAJADORES__#$TRABAJADORES#g" \
    "$CODIGO/despliegue/contanika.service" > /etc/systemd/system/contanika.service
systemctl daemon-reload
systemctl enable --now contanika
sleep 3
systemctl is-active --quiet contanika || { journalctl -u contanika -n 30 --no-pager; falla "El servicio no arrancó."; }

# ------------------------------------------------------------
# 9. nginx y certificado HTTPS
# ------------------------------------------------------------
paso "9/11 nginx y certificado HTTPS"
sed -e "s#__DOMINIO__#$DOMINIO#g" -e "s#__PUERTO__#$PUERTO_APP#g" \
    "$CODIGO/despliegue/nginx-contanika.conf" > /etc/nginx/sites-available/contanika
ln -sf /etc/nginx/sites-available/contanika /etc/nginx/sites-enabled/contanika
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
certbot --nginx --non-interactive --agree-tos --no-eff-email --redirect \
    -m "$CORREO_AVISOS" -d "$DOMINIO"

# ------------------------------------------------------------
# 10. Tareas automáticas y respaldos
# ------------------------------------------------------------
paso "10/11 Tareas automáticas y respaldo diario"
(cd "$CODIGO" && como_app bash scripts/instalar_cron.sh)
install -m 750 -o root -g root "$CODIGO/despliegue/respaldar.sh" /usr/local/sbin/contanika-respaldar
cat > /etc/cron.d/contanika-respaldo <<'EOF'
# Contanika: respaldo diario de la base y los archivos subidos (se guardan 14 días).
30 2 * * * root /usr/local/sbin/contanika-respaldar >> /var/log/contanika-respaldo.log 2>&1
EOF

# ------------------------------------------------------------
# 11. Despacho nuevo y primer Administrador
# ------------------------------------------------------------
paso "11/11 Creando el despacho y el Administrador"
gestionar cargar_datos_iniciales \
    --nombre-despacho "$NOMBRE_DESPACHO" \
    --ciudad-despacho "$CIUDAD_DESPACHO" \
    --nombre-admin "$NOMBRE_ADMIN" \
    --correo-admin "$CORREO_ADMIN"
# Fechas DIAN por último dígito del NIT: sin ellas no se calcula ningún vencimiento.
gestionar cargar_calendario_dian_2026

gestionar check --deploy --fail-level ERROR
if curl -fsS "https://$DOMINIO/salud/" >/dev/null; then
    ESTADO="responde bien"
else
    ESTADO="NO responde: revise con  journalctl -u contanika -n 50"
fi

cat <<EOF

============================================================
 Contanika quedó instalado.

   Dirección:            https://$DOMINIO   ($ESTADO)
   Panel de Django:      https://$DOMINIO/$RUTA_ADMIN
   Administrador:        $CORREO_ADMIN
                         (revise ese correo: trae el enlace para crear la
                          contraseña; vence en 3 días)

   Actualizar:           sudo bash $CODIGO/despliegue/actualizar.sh
   Ver errores:          journalctl -u contanika -n 50
   Respaldos:            /var/backups/contanika (cada día a las 2:30)

 Guarde una copia de $CODIGO/.env y $SECRETOS en un lugar
 seguro fuera del servidor: sin la clave de cifrado no se pueden leer
 las credenciales guardadas de los clientes.
============================================================
EOF
