# Instalar Contanika para un despacho nuevo

Contanika se instala **una vez por cada despacho**. Cada instalación tiene su
propia base de datos, su propio archivo `.env` y su propia dirección web. Los
datos de un despacho nunca se mezclan con los de otro.

Cuando un despacho paga la suscripción, usted prepara su instalación y crea su
**primer Administrador**. Desde ahí, el despacho se maneja solo: su
Administrador registra a sus colaboradores.

## Antes de empezar
Tenga a mano:
- El nombre del despacho y su ciudad.
- El nombre y el correo de la persona que será el Administrador.
- La cuenta de correo desde la que saldrán los correos del despacho (ver
  [CONFIGURAR_CORREO.md](CONFIGURAR_CORREO.md)).
- La dirección web que tendrá la instalación (por ejemplo
  `https://contanika.midespacho.co`).

## Pasos

### 1. Crear la base de datos
Cada despacho necesita una base de datos vacía y propia, ya sea en PostgreSQL
local o en un proyecto nuevo de Supabase. No reutilice la de otro despacho.

### 2. Preparar el `.env` de la instalación
Copie `.env.example` como `.env` y complete al menos:

| Variable | Qué poner |
|---|---|
| `ENTORNO` | `produccion` en un servidor; `local` para pruebas en su equipo |
| `SECRET_KEY` | Una clave nueva para esta instalación (ver el comando en el `.env.example`) |
| `CREDENCIAL_CLAVE_CIFRADO` | Una clave nueva para esta instalación (ver el comando en el `.env.example`) |
| `BD_*` | Los datos de la base de datos del paso 1 |
| `ALLOWED_HOSTS` | El dominio de la instalación |
| `URL_SITIO` | La dirección pública completa, con `https://` |
| `CORREO_*` | La cuenta de correo del despacho |

Las claves `SECRET_KEY` y `CREDENCIAL_CLAVE_CIFRADO` se generan **nuevas para
cada despacho**. Si se pierde la de cifrado, las credenciales guardadas de los
clientes ya no se pueden leer: guárdela en un lugar seguro.

### 3. Crear las tablas
```bash
python gestionar.py migrate
```

### 4. Cargar los datos iniciales y crear el Administrador
```bash
python gestionar.py cargar_datos_iniciales \
    --nombre-despacho "Contadores Asociados SAS" \
    --ciudad-despacho "Medellín" \
    --correo-admin gerente@contadoresasociados.co \
    --nombre-admin "María Gómez"
```

El comando:
- crea los roles, los módulos, los reportes, los permisos, los catálogos y las
  seis plantillas de documento;
- registra el despacho con ese nombre y esa ciudad;
- crea al Administrador **sin contraseña** y le envía un correo con un enlace
  para crearla él mismo. Usted nunca conoce su contraseña.

Si el correo no sale, la terminal muestra el enlace: cópielo y entrégueselo por
WhatsApp u otro medio. Sirve una sola vez y vence en 3 días. Si vence, el
Administrador puede pedir otro en «¿Olvidó su contraseña?».

El comando se puede correr de nuevo sin duplicar nada, y no cambia los datos
del despacho que ya existan.

Después cargue el calendario de la DIAN (fechas por último dígito del NIT).
**Sin este paso no se calcula ningún vencimiento** al crear los clientes:
```bash
python gestionar.py cargar_calendario_dian_2026
```

### 5. Revisar la instalación
```bash
python gestionar.py check --deploy
```

No debe quedar ningún aviso de `contanika.W001` (correo) ni de
`contanika.W002` (dirección). Luego abra `URL_SITIO/salud/`: debe responder
que el sistema está bien.

### 6. Entregar el sistema
El Administrador abre el enlace del correo, crea su contraseña y entra. Lo
primero que debe hacer:

1. **Documentos → Datos del despacho:** NIT, dirección, teléfono, correo y logo.
   Salen en el encabezado de todos los PDF.
2. **Equipo y roles → Usuarios → Nuevo usuario:** registrar a cada
   colaborador con su nombre, correo y rol (Contador Senior o Contador Junior).
   Cada uno recibe su propio enlace para crear su contraseña.
3. **Equipo y roles → Módulos por rol:** decidir qué ve cada rol.

## Preguntas frecuentes

**¿Quién registra a los colaboradores, usted o el despacho?**
El Administrador del despacho, desde Equipo y roles. Usted solo crea al primer
Administrador en el paso 4.

**Un colaborador no recibió el correo o el enlace venció.**
El Administrador pulsa «Reenviar enlace de acceso» (el sobre con la flecha en
el listado de usuarios). El colaborador también puede usar «¿Olvidó su
contraseña?».

**El despacho quiere un segundo Administrador.**
Lo crea su Administrador desde Equipo y roles, marcando la casilla de
confirmación.

**El despacho deja de pagar.**
Detenga su instalación. Antes, saque un respaldo de su base de datos y de su
carpeta `media/` para entregárselo o guardarlo según lo acordado.
