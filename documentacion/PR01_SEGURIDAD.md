# pr01 — Endurecimiento de seguridad de Contanika

Estado de los 20 controles al 7 de octubre de 2026. Para cada uno: qué había, qué se agregó y dónde se
prueba. Las pruebas nuevas están en `pruebas/seguridad/test_pr01.py`; las que recorren todas las rutas,
en `pruebas/seguridad/test_seguridad_transversal.py`.

**Estado:** Hecho = implementado y probado · Al desplegar = queda listo, se aplica en el servidor ·
Parcial = hay una parte que depende de una decisión.

| # | Control | Estado |
|---|---|---|
| 1 | Ocultar las claves API | Hecho |
| 2 | Eliminar secretos de Git | Hecho (una acción del usuario) |
| 3 | Usar una clave pública de BD | Al desplegar |
| 4 | Activar RLS | Al desplegar |
| 5 | Cifrar datos sensibles | Hecho |
| 6 | Forzar autenticación del servidor | Hecho |
| 7 | Restringir acceso a registros | Hecho |
| 8 | Bloquear manipulación de campos | Hecho |
| 9 | Proteger cookies de sesión | Hecho |
| 10 | Hashear contraseñas | Hecho |
| 11 | Limitar intentos de inicio de sesión | Hecho |
| 12 | Añadir protección contra bots | Parcial |
| 13 | Monitorizar consultas de BD | Hecho |
| 14 | Validar todas las entradas | Hecho |
| 15 | Escapar contenido del usuario | Hecho |
| 16 | Restringir subida de archivos | Hecho |
| 17 | Limitar respuestas de API | Hecho |
| 18 | Añadir cabeceras de seguridad | Hecho |
| 19 | Forzar HTTPS | Al desplegar |
| 20 | Escanear dependencias | Hecho |

## Detalle por control

### 1. Ocultar las claves API
- **Había:** todas las claves se leen del archivo `.env`, que no se versiona.
- **Se agregó:** en producción el sistema no arranca si falta la `SECRET_KEY`, si es la de desarrollo o
  si es corta; tampoco sin `CREDENCIAL_CLAVE_CIFRADO` ni `ALLOWED_HOSTS`. Ninguna clave llega al
  navegador: Contanika no usa la API de Supabase desde el cliente.

### 2. Eliminar secretos de Git
- **Había:** `.env`, `CREDENCIALES_PRUEBA.md`, `media/` y los registros están en `.gitignore` y nunca se
  subieron.
- **Se encontró:** la contraseña de desarrollo de la usuaria administradora estaba escrita en
  `AGENTS.md`. Se retiró.
- **Se agregó:** una prueba que falla si un archivo versionado trae una contraseña o una clave escrita.
- **Acción del usuario:** esa contraseña sigue en el historial de Git (el repositorio es privado).
  Cámbiela en el entorno local y no la use nunca en producción. Borrarla del historial exige reescribirlo;
  no se hizo.

### 3. Usar una clave pública de BD
- En Supabase, la «clave pública» (anon) es la que puede ir en un navegador. Contanika no la usa: el
  servidor se conecta directo a PostgreSQL y el navegador nunca ve una clave de base de datos.
- **Se agregó:** `scripts/bd/03_rol_aplicacion.sql` crea dos roles de privilegios mínimos:
  `contanika_dueno` (solo para migraciones) y `contanika_app` (el que usa el sistema: lee y escribe
  filas, no altera tablas). En producción el sistema se niega a arrancar con el superusuario `postgres`.
- **Al desplegar:** ejecutar el script con contraseñas propias.
- **Ensayado (11-oct-2026):** en un PostgreSQL temporal que imita a Supabase (allá `postgres` no es
  superusuario y existen los roles públicos `anon` y `authenticated`) se corrió la secuencia completa:
  script 03, migraciones como `contanika_dueno`, script 03 otra vez, script 04, datos iniciales y
  `check --deploy` como `contanika_app`. El ensayo destapó que los scripts fallaban porque `postgres` no
  podía tocar las tablas del dueño; el script 03 ahora lo hace miembro de ese rol. `contanika_app` lee y
  escribe pero no crea, altera ni borra tablas. Por el pooler de Supabase el usuario se escribe
  `contanika_app.<referencia del proyecto>`; `postgres.<referencia>` también se rechaza.

### 4. Activar RLS
- **Por qué importa:** Supabase publica cada tabla por su API con la clave pública. Sin RLS, quien
  tenga esa clave podría leer las tablas sin pasar por Contanika.
- **Se agregó:** `scripts/bd/04_activar_rls.sql` activa RLS en todas las tablas, deja pasar solo a los
  roles de la aplicación y le quita los privilegios a los roles públicos de Supabase. Quién ve qué
  dentro del sistema lo sigue decidiendo Contanika.
- **Probado:** en el ensayo del control 3: las 53 tablas (las 42 de Contanika y las de Django) quedan
  con RLS y su política, `anon` y `authenticated` no pueden leer ninguna, y el script se puede repetir.
- **Al desplegar:** ejecutarlo después de las migraciones, y de nuevo cuando una migración cree tablas.

### 5. Cifrar datos sensibles
- **Había:** contraseñas de usuarios con hash; credenciales de portales de clientes cifradas (Fernet);
  conexión a la base de datos de producción con `sslmode=require`.
- **Se agregó:** producción exige la clave de cifrado; HTTPS obligatorio cifra todo el tráfico.
- **Queda como está, por decisión del 1-oct-2026:** el correo de bienvenida lleva la contraseña
  temporal. Recomendación: que el usuario la cambie al entrar.

### 6. Forzar autenticación del servidor
- **Había:** toda vista exige sesión (probado en todas las rutas).
- **Se encontró:** en desarrollo, cualquier archivo de `media/` (cuentas de cobro, certificados,
  adjuntos) se podía abrir por dirección sin iniciar sesión; y en producción las fotos, firmas y el
  membrete no se habrían visto.
- **Se agregó:** los archivos subidos pasan por una vista que exige sesión. Solo entrega la foto y la
  firma a su dueño o al Administrador, y el membrete a cualquier usuario. Documentos, cuentas de cobro y
  adjuntos solo se descargan por la vista de su módulo, que valida rol y cliente.

### 7. Restringir acceso a registros
- **Había:** cada módulo consulta por selectores según el rol; quien pide un registro que no le
  corresponde recibe 404 o 403. Probado por módulo y, para rol y módulo, en todas las rutas.

### 8. Bloquear manipulación de campos
- **Había:** cada formulario declara sus campos; lo que llegue de más en la petición se ignora. El
  Contador Junior no recibe los campos de responsable ni de estado del cliente. Los abonos no se
  modifican ni se borran (disparador de la base de datos).

### 9. Proteger cookies de sesión
- **Había:** cookies seguras en producción.
- **Se agregó:** `HttpOnly` y `SameSite=Lax` en todos los entornos; la sesión vence tras 8 horas sin uso
  (`SESION_DURACION_HORAS`) y al cerrar el navegador; en producción las cookies llevan el prefijo
  `__Host-`.
- **Cambio visible:** hay que volver a iniciar sesión al reabrir el navegador.

### 10. Hashear contraseñas
- **Había:** PBKDF2 con sal (el de Django) y validadores: mínimo 10 caracteres, no comunes, no solo
  números, no parecidas a los datos del usuario.

### 11. Limitar intentos de inicio de sesión
- **Había:** django-axes bloquea tras 5 intentos fallidos, durante 1 hora.
- **Se agregó:** la prueba que faltaba y el registro de los bloqueos en `registros/seguridad.log`.

### 12. Añadir protección contra bots
- **Se agregó:** campo señuelo en el inicio de sesión (los robots que rellenan todos los campos quedan
  rechazados); `robots.txt` y la cabecera `X-Robots-Tag` para que el sistema no aparezca en buscadores
  (desde el 11-oct-2026 la única excepción es la página web de inicio, `/`, que es pública);
  la dirección del panel de administración de Django se puede cambiar con `RUTA_ADMIN`; tope de
  peticiones en el enlace público del PDF.
- **Decisión pendiente:** un CAPTCHA (por ejemplo Cloudflare Turnstile o reCAPTCHA) exige crear una
  cuenta y sus claves en un servicio externo. Con el bloqueo por intentos y el señuelo, para un sistema
  interno con pocos usuarios es razonable no ponerlo.

### 13. Monitorizar consultas de BD
- **Se agregó:** cada consulta que tarde más de 500 ms (`BD_CONSULTA_LENTA_MS`) y cada petición con más
  de 150 consultas (`BD_MAXIMO_CONSULTAS`) quedan en `registros/consultas.log`, sin los parámetros para
  no dejar datos de clientes en el registro. Los accesos denegados, errores y CSRF rechazados van a
  `registros/seguridad.log`.
- **Al desplegar:** en Supabase, activar además `pg_stat_statements` desde su panel.

### 14. Validar todas las entradas
- **Había:** toda entrada pasa por un formulario de Django con sus validaciones; los filtros de los
  listados también.
- **Se agregó:** topes al tamaño de la petición y al número de campos y de archivos.

### 15. Escapar contenido del usuario
- **Había:** las plantillas escapan todo por defecto; el único `mark_safe` (texto del certificado) recibe
  variables ya escapadas; los datos de los gráficos van con `json_script`.
- **Se agregó:** política de seguridad de contenido (CSP), que impide cargar código de otros servidores
  aunque se colara contenido malicioso.

### 16. Restringir subida de archivos
- **Había:** lista de extensiones permitidas y tamaño máximo (10 MB adjuntos, 5 MB Excel, 2 MB imágenes).
- **Se agregó:** se comprueba que el contenido sea del formato que dice la extensión (un programa
  renombrado como `.pdf` se rechaza); las imágenes solo pueden ser JPG o PNG; los archivos se guardan
  sin permiso de ejecución y no se publican por dirección.

### 17. Limitar respuestas de API
- **Había:** todos los listados van paginados; las notificaciones traen como máximo 15; los reportes
  muestran 200 filas por sección en pantalla.
- **Se agregó:** tope de peticiones por minuto en la API (30 sin sesión, 300 con sesión) y en el enlace
  público del PDF (20 por dirección IP; al pasarse responde 429).

### 18. Añadir cabeceras de seguridad
- **Se agregó en todos los entornos:** `Content-Security-Policy`, `X-Frame-Options: DENY`,
  `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Cross-Origin-Opener-Policy`,
  `Permissions-Policy` (sin cámara, micrófono, ubicación ni pagos) y `X-Robots-Tag`.
- **Se agregó:** huella de integridad (SRI) en Bootstrap, los íconos y Chart.js: si el CDN entregara un
  archivo alterado, el navegador no lo ejecuta.
- **Limitación conocida:** la CSP permite scripts y estilos en línea (`'unsafe-inline'`), porque las
  plantillas los usan. Quitarlo exige pasar esos scripts a archivos; es una mejora futura.

### 19. Forzar HTTPS
- **Había:** en producción, redirección a HTTPS, HSTS de un año con subdominios y cookies seguras.
- **Al desplegar:** se activa solo con la configuración de producción (`ENTORNO=produccion`).

### 20. Escanear dependencias
- **Había:** `pip-audit` y `bandit` en `scripts/calidad.sh`.
- **Se agregó:** Dependabot (revisión semanal de las librerías) y un flujo de GitHub Actions que corre
  `bandit` y `pip-audit` en cada cambio y cada lunes.

## Pasos al desplegar en producción

1. Generar una `SECRET_KEY` y una `CREDENCIAL_CLAVE_CIFRADO` nuevas en el `.env` del servidor.
2. Ejecutar `scripts/bd/03_rol_aplicacion.sql` con contraseñas propias.
3. Migrar con `BD_USUARIO=contanika_dueno`; repetir la sección «Privilegios» del script 03.
4. Ejecutar `scripts/bd/04_activar_rls.sql` y comprobar que no lista tablas sin RLS.
5. Dejar `BD_USUARIO=contanika_app`, `ALLOWED_HOSTS`, `CSRF_ORIGENES_CONFIABLES` y `URL_SITIO` con el
   dominio real, y una `RUTA_ADMIN` distinta de `admin/`.
6. Correr `python gestionar.py check --deploy`: no debe dejar avisos.
