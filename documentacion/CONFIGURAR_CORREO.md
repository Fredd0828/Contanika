# Configurar el correo de Contanika

Contanika usa el correo para cuatro cosas: el enlace con el que cada usuario
crea su contraseña, «¿Olvidó su contraseña?», las alertas de vencimientos y las
cuentas de cobro. Mientras `CORREO_HOST` esté vacío, en el equipo local los
correos solo aparecen en la consola donde corre `runserver`. No llegan a nadie.

Para que salgan de verdad basta con darle a Contanika una cuenta de correo y su
contraseña de aplicación. No hay que programar nada.

## Con una cuenta de Gmail

### 1. Activar la verificación en dos pasos
Google solo entrega contraseñas de aplicación a cuentas con verificación en dos
pasos.

1. En el teléfono o computador donde usa esa cuenta normalmente, abra
   <https://myaccount.google.com/security>.
2. En «Cómo inicias sesión en Google», active **Verificación en dos pasos** y
   siga las instrucciones.

Si Google bloquea la activación desde un equipo nuevo, hágalo desde el
dispositivo de siempre: Google desconfía de los equipos que no conoce.

### 2. Crear la contraseña de aplicación
1. Abra <https://myaccount.google.com/apppasswords>.
2. En el nombre escriba `Contanika` y pulse **Crear**.
3. Google muestra 16 letras en cuatro grupos (por ejemplo `abcd efgh ijkl mnop`).
   Cópielas: solo se muestran una vez.

Esa contraseña solo sirve para enviar correo desde Contanika. No es la
contraseña de la cuenta, y se puede revocar en la misma página sin afectar nada
más.

### 3. Escribirla en el `.env`
Abra el archivo `.env` de la carpeta `codigo/` y deje estas líneas así:

```ini
CORREO_HOST=smtp.gmail.com
CORREO_PUERTO=587
CORREO_USUARIO=la-cuenta@gmail.com
CORREO_CLAVE=abcdefghijklmnop
CORREO_REMITENTE=Contanika <la-cuenta@gmail.com>
```

- `CORREO_CLAVE` lleva las 16 letras **sin espacios**.
- `CORREO_REMITENTE` debe usar la misma cuenta: Gmail cambia el remitente si no
  coincide.
- El archivo `.env` nunca se sube a GitHub (está en `.gitignore`).

### 4. Reiniciar el servidor
Detenga `runserver` (Ctrl+C) y vuelva a iniciarlo. Django lee el `.env` solo al
arrancar.

### 5. Probar el envío
Desde `codigo/`, con el entorno virtual activo:

```bash
python gestionar.py sendtestemail su-correo@ejemplo.co
```

Si llega un correo de prueba a esa bandeja, el correo funciona. Si sale un error:

| Error | Qué significa | Qué hacer |
|---|---|---|
| `Username and Password not accepted` | La contraseña de aplicación está mal o tiene espacios | Créela de nuevo y péguela sin espacios |
| `Connection refused` o `timed out` | No se pudo conectar con Gmail | Revise `CORREO_HOST=smtp.gmail.com` y `CORREO_PUERTO=587`, y la conexión a internet |
| El comando no falla pero el correo no llega | Llegó al correo no deseado | Revise esa carpeta y marque el mensaje como «No es spam» |

## Límites de Gmail
Una cuenta gratuita de Gmail envía hasta unos 500 correos al día. Un despacho
pequeño no se acerca a ese límite: las alertas, las cuentas de cobro del mes y
los enlaces de acceso suman pocas decenas. Si un día se pasa, Gmail deja de
enviar hasta el día siguiente. Las cuentas de cobro que no salgan quedan como
fallidas en Honorarios y se pueden reintentar.

## En producción (una instalación por despacho)
Cada despacho que use Contanika tiene su propia instalación y su propio `.env`.
Lo ideal es que cada uno envíe desde su propia cuenta, para que sus clientes
reciban las cuentas de cobro a nombre del despacho:

- **Gmail o Google Workspace del despacho:** los mismos pasos de arriba con la
  cuenta del despacho.
- **Un dominio propio** (por ejemplo `cobros@midespacho.co`): el proveedor del
  dominio da el servidor SMTP, el puerto y la contraseña; se escriben en las
  mismas variables `CORREO_*`.

En el servidor también hay que escribir la dirección pública en `URL_SITIO`
(por ejemplo `URL_SITIO=https://contanika.midespacho.co`). Con la dirección
local, los enlaces de los correos no abren fuera del equipo.

`python gestionar.py check --deploy` avisa si falta alguna de las dos cosas
(avisos `contanika.W001` y `contanika.W002`).
