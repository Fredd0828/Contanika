#!/usr/bin/env bash
# ============================================================
# Contanika - Actualizar el servidor con lo último de GitHub (main).
#
# Uso, como root:  sudo bash /srv/contanika/codigo/despliegue/actualizar.sh
#
# Hace un respaldo antes de tocar nada, baja el código, instala librerías,
# aplica migraciones (con el dueño de las tablas), vuelve a aplicar los
# privilegios y RLS (por si hay tablas nuevas), recolecta estáticos y
# reinicia el servicio.
# ============================================================
set -euo pipefail

USUARIO=contanika
CODIGO=/srv/contanika/codigo
PYTHON=$CODIGO/.venv/bin/python
SECRETOS=/root/contanika-secretos.env
BD=contanika_bd

paso() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
falla() { printf '\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }
como_app() { sudo -u "$USUARIO" -H "$@"; }
gestionar() { (cd "$CODIGO" && como_app "$PYTHON" gestionar.py "$@"); }
sql() { sudo -u postgres env PGOPTIONS="-c client_min_messages=warning" psql -v ON_ERROR_STOP=1 -q "$@"; }

[[ $EUID -eq 0 ]] || falla "Ejecútelo como root: sudo bash $0"
[[ -f "$SECRETOS" ]] || falla "No existe $SECRETOS (lo crea instalar_vps.sh)."
# shellcheck disable=SC1090
. "$SECRETOS"
cd /tmp

paso "Respaldo previo"
/usr/local/sbin/contanika-respaldar

paso "Bajando el código"
ANTES=$(como_app git -C "$CODIGO" rev-parse --short HEAD)
como_app git -C "$CODIGO" pull --ff-only --quiet
AHORA=$(como_app git -C "$CODIGO" rev-parse --short HEAD)
echo "Versión: $ANTES -> $AHORA"

paso "Librerías de Python"
como_app "$CODIGO/.venv/bin/pip" install --quiet -r "$CODIGO/requirements.txt"

paso "Migraciones, privilegios y RLS"
(cd "$CODIGO" && como_app env BD_USUARIO=contanika_dueno BD_CLAVE="$BD_CLAVE_DUENO" \
    "$PYTHON" gestionar.py migrate --noinput)
sql -d "$BD" < "$CODIGO/scripts/bd/03_rol_aplicacion.sql"
sql -d "$BD" < "$CODIGO/scripts/bd/04_activar_rls.sql" >/dev/null
gestionar collectstatic --noinput -v 0
# El calendario DIAN NO se recarga aquí: el Administrador lo sube cada año
# desde Calendario → Tabla DIAN y puede corregir fechas a mano; recargarlo
# desde el código desharía esas correcciones.
install -m 750 -o root -g root "$CODIGO/despliegue/respaldar.sh" /usr/local/sbin/contanika-respaldar

paso "nginx: rechazo por HTTPS de nombres ajenos"
REGLA_443=/etc/nginx/conf.d/contanika-rechazo-443.conf
install -m 644 -o root -g root "$CODIGO/despliegue/nginx-rechazo-443.conf" "$REGLA_443"
if nginx -t 2>/dev/null; then
    systemctl reload nginx
    echo "Regla activa: por HTTPS solo responde el dominio del sistema."
else
    # Si este nginx no la acepta, se quita y el sitio sigue como estaba.
    rm -f "$REGLA_443"
    echo "Aviso: nginx no aceptó la regla de rechazo; se quitó y el sitio sigue igual."
fi

paso "Reiniciando"
gestionar check --deploy --fail-level ERROR
systemctl restart contanika
sleep 3
systemctl is-active --quiet contanika || { journalctl -u contanika -n 30 --no-pager; falla "El servicio no arrancó."; }
DOMINIO=$(grep -E '^URL_SITIO=' "$CODIGO/.env" | cut -d= -f2-)
curl -fsS "$DOMINIO/salud/" >/dev/null && echo "Listo: $DOMINIO responde ($AHORA)."
