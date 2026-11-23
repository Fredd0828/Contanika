# Subir Contanika a un VPS

Esta guía deja Contanika funcionando en internet, con HTTPS, en un servidor
propio (VPS) con Ubuntu 24.04. La instalación la hace un solo script; usted
solo contrata el servidor, crea la dirección y responde unas preguntas.

Tiempo aproximado: 30 a 45 minutos, la primera vez.

---

## Qué necesita antes de empezar

| Qué | Para qué |
|---|---|
| Un VPS con **Ubuntu 24.04**, 1 vCPU y **2 GB de RAM o más** | Donde corre Contanika y su base de datos |
| Una dirección gratis en **duckdns.org** | Para abrir el sistema con un nombre y tener HTTPS |
| La **contraseña de aplicación** de Gmail | Para que salgan los correos (ver `CONFIGURAR_CORREO.md`) |
| El **correo del Administrador** del despacho | Ahí le llega el enlace para crear su contraseña |

---

## Paso 1. Contratar el VPS

Cualquier proveedor sirve si ofrece Ubuntu 24.04. Opciones conocidas:
Hostinger (KVM 1), Hetzner (CX22) o DigitalOcean (2 GB). Al crearlo:

1. Sistema operativo: **Ubuntu 24.04 LTS** (sin panel de control ni aplicaciones extra).
2. Ubicación: la más cercana a Colombia que ofrezca (Estados Unidos o Brasil).
3. Acceso: el proveedor le pide una **contraseña de root**; guárdela bien.
4. Anote la **dirección IP** del servidor (por ejemplo `203.0.113.10`).

## Paso 2. Crear la dirección en DuckDNS

1. Entre a https://www.duckdns.org e inicie sesión con su cuenta de Google o GitHub.
2. En «sub domain» escriba un nombre, por ejemplo `contanika-prueba`, y pulse **add domain**.
3. En la fila que aparece, en «current ip», escriba la **IP del VPS** y pulse **update ip**.
4. Su dirección queda así: `contanika-prueba.duckdns.org`.

Espere unos minutos a que la dirección empiece a responder.

## Paso 3. Entrar al servidor

Desde Windows abra **PowerShell** y escriba (con la IP de su VPS):

```
ssh root@203.0.113.10
```

La primera vez pregunta si confía en el servidor: escriba `yes`. Luego pide la
contraseña de root (no se ve mientras la escribe).

## Paso 4. Instalar Contanika

Ya dentro del servidor, copie y pegue estas dos líneas:

```
curl -fsSLO https://raw.githubusercontent.com/Fredd0828/Contanika/main/despliegue/instalar_vps.sh
bash instalar_vps.sh
```

El script pregunta:

1. La dirección (`contanika-prueba.duckdns.org`).
2. Un correo para los avisos del certificado HTTPS.
3. El nombre y la ciudad del despacho.
4. El nombre y el correo del Administrador.
5. La cuenta de Gmail que envía los correos y su contraseña de aplicación
   (no se ve mientras la pega).

Después trabaja solo durante unos 10 a 20 minutos. Al terminar muestra la
dirección del sistema y la del panel de Django.

## Paso 5. Primer ingreso

1. El Administrador recibe un correo con el enlace para **crear su contraseña**
   (vence en 3 días). Si no llega, revise Spam.
2. Entra a `https://contanika-prueba.duckdns.org` con su correo y su contraseña.
3. Carga los **Datos del despacho** (logo, NIT, dirección, teléfono y correo).
4. Crea a los colaboradores en **Equipo y roles**: a cada uno le llega su enlace.

## Paso 6. Guardar los secretos fuera del servidor

El script generó claves que no se pueden recuperar si se pierde el servidor.
Desde PowerShell, en su computador, descárguelas a una carpeta segura:

```
scp root@203.0.113.10:/srv/contanika/codigo/.env  contanika-produccion.env
scp root@203.0.113.10:/root/contanika-secretos.env  contanika-secretos.env
```

No las suba a GitHub ni las envíe por chat. Sin `CREDENCIAL_CLAVE_CIFRADO` no
se pueden leer las credenciales guardadas de los clientes.

---

## Actualizar el servidor con cambios nuevos

Cada vez que se mergea algo en `main` en GitHub:

```
ssh root@203.0.113.10
bash /srv/contanika/codigo/despliegue/actualizar.sh
```

Hace un respaldo, baja el código, aplica migraciones y reinicia. Tarda uno o
dos minutos. Si lo que baja trae una versión nueva de `actualizar.sh`, avisa
«Este script cambió con la actualización» y sigue con esa versión, sin repetir
el respaldo.

## Respaldos

Cada día a las 2:30 a. m. se guardan la base de datos y los archivos subidos
en `/var/backups/contanika` (se conservan 14 días). Para descargar el último:

```
scp "root@203.0.113.10:/var/backups/contanika/*" .\respaldos-contanika\
```

### Restaurar un respaldo

Solo si hay que volver a un estado anterior. Como root, una línea a la vez,
cambiando `AAAA-MM-DD` por la fecha del respaldo:

```
systemctl stop contanika
sudo -u postgres dropdb --force contanika_bd
sudo -u postgres createdb -E UTF8 -T template0 contanika_bd
sudo -u postgres pg_restore -d contanika_bd /var/backups/contanika/contanika_AAAA-MM-DD.dump
sudo -u postgres psql -q -d contanika_bd < /srv/contanika/codigo/scripts/bd/03_rol_aplicacion.sql
sudo -u postgres psql -q -d contanika_bd < /srv/contanika/codigo/scripts/bd/04_activar_rls.sql
tar -xzf /var/backups/contanika/media_AAAA-MM-DD.tar.gz -C /srv/contanika/codigo
systemctl start contanika
```

No use `pg_restore --clean`: no borra lo que se creó después del respaldo y la
base queda dañada. Si además hay que volver a una versión anterior del código,
antes de `systemctl start contanika`:

```
sudo -u contanika git -C /srv/contanika/codigo checkout v1.0.0
sudo -u contanika /srv/contanika/codigo/.venv/bin/pip install -q -r /srv/contanika/codigo/requirements.txt
cd /srv/contanika/codigo && sudo -u contanika .venv/bin/python gestionar.py collectstatic --noinput -v 0
```

(con la etiqueta que corresponda). Para volver después a la última versión:
`sudo -u contanika git -C /srv/contanika/codigo checkout main` y luego
`actualizar.sh`.

## Qué quedó instalado

| Pieza | Detalle |
|---|---|
| Código | `/srv/contanika/codigo`, del usuario `contanika` (sin permisos de administrador) |
| Aplicación | Servicio `contanika` (gunicorn), solo escucha dentro del servidor |
| Web | nginx con HTTPS de Let's Encrypt; el certificado se renueva solo. Quien entra por la IP o con otro nombre no recibe respuesta, ni por HTTP ni por HTTPS (`/etc/nginx/conf.d/contanika-rechazo-443.conf`) |
| Base de datos | PostgreSQL en el mismo servidor, cerrado a internet; usuario `contanika_app` sin permiso para crear o borrar tablas; RLS activo |
| Cortafuegos | Solo SSH (22), HTTP (80) y HTTPS (443) |
| Tareas automáticas | Cobros cada 15 minutos y alertas cada hora (cron del usuario `contanika`) |
| Calendario DIAN 2026 | Fechas por último dígito del NIT, para calcular los vencimientos. Cada año el Administrador sube el nuevo en **Calendario → Tabla DIAN** (plantilla de Excel) y luego pulsa **Calcular vencimientos DIAN** en la lista |
| Actualizaciones de Ubuntu | Las de seguridad se instalan solas |

## Si algo falla

| Síntoma | Qué revisar |
|---|---|
| El script dice que el dominio no apunta al servidor | En DuckDNS, la IP debe ser la del VPS. Espere 5 minutos y repita. |
| Falla el certificado HTTPS | Lo mismo: la dirección debe apuntar al VPS y el puerto 80 debe estar abierto en el panel del proveedor. |
| La página muestra «502 Bad Gateway» | `journalctl -u contanika -n 50` muestra el error de la aplicación. |
| No llegan los correos | Revise `CORREO_*` en `/srv/contanika/codigo/.env` y reinicie con `systemctl restart contanika`. |
| Quiere ver los errores de la aplicación | `tail -n 50 /srv/contanika/codigo/registros/*.log` |
| Se bloqueó el inicio de sesión por intentos | Espere 15 minutos, o como root: `cd /srv/contanika/codigo && sudo -u contanika .venv/bin/python gestionar.py axes_reset` |
