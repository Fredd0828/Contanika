#!/usr/bin/env bash
# ============================================================
# Contanika - Respaldo diario de la base y de los archivos subidos.
#
# Lo instala instalar_vps.sh en /usr/local/sbin/contanika-respaldar y lo
# corre el cron cada día a las 2:30. Guarda en /var/backups/contanika:
#   contanika_AAAA-MM-DD.dump   base de datos (pg_dump, formato propio)
#   media_AAAA-MM-DD.tar.gz     logos, firmas, fotos y adjuntos
# y borra los de más de 14 días.
#
# Restaurar (como root). No use pg_restore --clean: no borra lo que se creó
# después del respaldo y la base queda dañada (defecto DEF-002). Se restaura
# sobre una base vacía y luego se reaplican privilegios y RLS:
#   systemctl stop contanika
#   sudo -u postgres dropdb --force contanika_bd
#   sudo -u postgres createdb -E UTF8 -T template0 contanika_bd
#   sudo -u postgres pg_restore -d contanika_bd /var/backups/contanika/contanika_AAAA-MM-DD.dump
#   sudo -u postgres psql -q -d contanika_bd < /srv/contanika/codigo/scripts/bd/03_rol_aplicacion.sql
#   sudo -u postgres psql -q -d contanika_bd < /srv/contanika/codigo/scripts/bd/04_activar_rls.sql
#   tar -xzf /var/backups/contanika/media_AAAA-MM-DD.tar.gz -C /srv/contanika/codigo
#   systemctl start contanika
# ============================================================
set -euo pipefail

DESTINO=/var/backups/contanika
CODIGO=/srv/contanika/codigo
FECHA=$(date +%F)

install -d -m 700 -o root -g root "$DESTINO"
sudo -u postgres pg_dump -Fc contanika_bd > "$DESTINO/contanika_$FECHA.dump"
tar -czf "$DESTINO/media_$FECHA.tar.gz" -C "$CODIGO" media
chmod 600 "$DESTINO"/*_"$FECHA".*
find "$DESTINO" -type f -mtime +14 -delete
echo "$(date '+%F %T') respaldo listo: $(du -sh "$DESTINO" | cut -f1) en total"
