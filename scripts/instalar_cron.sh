#!/usr/bin/env bash
# ============================================================
# Contanika - Programa las tareas automáticas en cron
#
#   procesar_cobros   cada 15 minutos: marca cuentas vencidas, genera el
#                     cobro mensual, programa recordatorios y despacha los
#                     envíos cuya hora llegó (Módulo 6).
#   procesar_alertas  cada hora: envía las alertas de vencimientos por
#                     correo y registra las internas (Módulo 2, HU040).
#
# Uso (desde la carpeta codigo/):
#   bash scripts/instalar_cron.sh            instala o actualiza
#   bash scripts/instalar_cron.sh --ver      muestra lo que instalaría
#   bash scripts/instalar_cron.sh --quitar   retira las tareas
#
# Es idempotente: las líneas quedan entre dos marcas y se reemplazan en
# cada corrida, sin tocar el resto del crontab del usuario. La salida de
# cada comando queda en registros/cron_*.log.
#
# En WSL cron solo corre mientras Ubuntu esté abierto. Verifique que el
# servicio esté activo con: service cron status
# ============================================================
set -euo pipefail

RUTA="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$RUTA/.venv/bin/python"
REGISTROS="$RUTA/registros"
INICIO="# >>> contanika (no editar a mano: scripts/instalar_cron.sh) >>>"
FIN="# <<< contanika <<<"

bloque() {
    cat <<EOF
$INICIO
*/15 * * * * cd "$RUTA" && "$PYTHON" gestionar.py procesar_cobros >> "$REGISTROS/cron_cobros.log" 2>&1
0 * * * * cd "$RUTA" && "$PYTHON" gestionar.py procesar_alertas >> "$REGISTROS/cron_alertas.log" 2>&1
$FIN
EOF
}

# Crontab actual sin el bloque de Contanika (vacío si el usuario no tiene crontab).
sin_bloque() {
    (crontab -l 2>/dev/null || true) | sed "/^$INICIO\$/,/^$FIN\$/d"
}

case "${1:-}" in
    --ver)
        bloque
        ;;
    --quitar)
        sin_bloque | crontab -
        echo "Tareas de Contanika retiradas del crontab."
        ;;
    "")
        if [ ! -x "$PYTHON" ]; then
            echo "No se encontró el entorno virtual en $PYTHON" >&2
            exit 1
        fi
        mkdir -p "$REGISTROS"
        { sin_bloque; bloque; } | crontab -
        echo "Tareas de Contanika instaladas. Crontab actual:"
        crontab -l
        ;;
    *)
        echo "Opción no reconocida: $1 (use --ver o --quitar)" >&2
        exit 2
        ;;
esac
