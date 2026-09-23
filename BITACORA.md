# Bitácora de trabajo — Contanika

Registro diario del avance de la Fase 3 (Ejecución) y Fase 4 (Evaluación).
Cada entrada indica qué se hizo, cómo verificarlo, el resultado de las pruebas,
las evidencias y los pendientes. Esta bitácora es la base de los numerales
3.1, 3.2 y 3.3 del documento de proyecto.

---

## Glosario de comandos

| Comando | Qué hace |
|---|---|
| `cd .../codigo` | Entra a la carpeta del proyecto. |
| `source .venv/bin/activate` | Activa el entorno virtual (herramientas aisladas del proyecto). |
| `python gestionar.py runserver` | Enciende el servidor web local. Se detiene con `Ctrl+C`. |
| `python gestionar.py migrate` | Aplica a la base de datos los cambios de estructura. |
| `python gestionar.py makemigrations` | Genera los cambios de estructura a partir de los modelos. |
| `python gestionar.py cargar_datos_iniciales` | Carga roles, módulos, reportes y catálogos base. |
| `python gestionar.py changepassword <correo>` | Cambia la contraseña de un usuario. |
| `bash scripts/calidad.sh` | Ejecuta estilo, seguridad y pruebas con cobertura. |
| `PGPASSWORD=... psql -h 127.0.0.1 -U contanika -d contanika_bd` | Abre la consola de PostgreSQL. |
| `\dt` (dentro de psql) | Lista las tablas de la base de datos. |
| `git log --oneline` | Muestra el historial de versiones del proyecto. |

---

## Lunes 21 de septiembre de 2026 — Arranque de la Fase 3

**Objetivo del día:** dejar lista la base del sistema (entorno, base de datos,
las 36 tablas, autenticación y el mecanismo de calidad).

### Trabajo realizado

1. **Entorno y proyecto**
   - Repositorio Git inicializado en `codigo/` con rama `principal`.
   - Entorno virtual con Python 3.12 y dependencias del stack (Django 5.2 LTS,
     DRF, psycopg, ReportLab, openpyxl, Pillow, django-axes, entre otras).
   - Configuración separada por entornos: `config/settings/base.py`,
     `local.py` y `produccion.py`; credenciales en variables de entorno (`.env`).
2. **Base de datos (entregable 3.1, inicio)**
   - Las 36 tablas del diccionario de datos (numeral 2.5) modeladas y migradas
     a PostgreSQL. Script documentado en `scripts/bd/01_esquema_contanika.sql`
     y datos iniciales en `scripts/bd/02_datos_iniciales.sql`.
3. **Seguridad y autenticación (RQF001, RQNF004)**
   - Modelo de usuario propio con contraseña cifrada, roles del despacho
     (Administrador, Contador Senior, Contador Junior) y sesiones de Django.
   - Permisos configurables por módulo y por reporte (RQF031).
   - Bloqueo de fuerza bruta con django-axes.
   - Pantalla de inicio de sesión, panel principal y cierre de sesión.
4. **Datos iniciales**
   - 3 roles, 10 módulos, 6 reportes, permisos por rol, catálogos de servicios,
     métodos de pago, conceptos facturables y las 6 plantillas base.
5. **Calidad**
   - `scripts/calidad.sh` con ruff (estilo), bandit (seguridad del código),
     pip-audit (dependencias) y pytest (pruebas + cobertura).

### Decisión de la sesión

- Se migró de Django 4.2 LTS a **Django 5.2 LTS**: la serie 4.2 terminó su
  soporte en abril de 2026 y `pip-audit` reportó 7 vulnerabilidades sin parche.
  Queda pendiente actualizar D1 y RQNF002 del documento Word ("Django 4.2 LTS"
  debe decir "Django 5.2 LTS").

### Cómo verificarlo (entorno local)

```bash
cd /home/fredd/documentos/ubuntu/contanika/codigo
source .venv/bin/activate
python gestionar.py runserver
```

- `http://127.0.0.1:8000` → pantalla de inicio de sesión.
- Iniciar sesión (ver `CREDENCIALES_PRUEBA.md`) → panel con los 10 módulos.
- `http://127.0.0.1:8000/admin/` → las 36 tablas con los datos iniciales.
- `bash scripts/calidad.sh` → pruebas y análisis de calidad.

### Resultado de las pruebas

- 24 pruebas unitarias y de seguridad: **24 aprobadas**.
- Cobertura de código: **93 %**.
- Ruff: sin hallazgos. Bandit: sin hallazgos. pip-audit: sin vulnerabilidades.

### Evidencias

- `evidencias/00-inicio/` (capturas de login, panel y administración).
- `scripts/bd/01_esquema_contanika.sql` (entregable 3.1).
- `git log --oneline` → commit `48ac78e`.

### Pendientes

- Cambiar la contraseña temporal de `paula@befrec.co`.
- Actualizar D1 y RQNF002 del Word a Django 5.2 LTS.

---

## Lunes 21 de septiembre de 2026 — Módulo 1, bloque 1

**Objetivo del bloque:** dejar navegable la gestión básica de clientes (CU002,
HU001–HU003): listar, filtrar, crear, editar, consultar e inactivar.

### Trabajo realizado

1. **Listado de clientes** con filtros desplegables por ciudad, municipio,
   régimen tributario, tipo de persona, responsable, estado y rango de fechas
   de registro, con paginación y conteo de resultados.
2. **Ficha del cliente**: creación y edición con nombre o razón social, NIT o
   cédula (sin duplicados), tipo de persona, régimen tributario, responsable
   de IVA, ciudad, municipio principal, contacto, responsable asignado y estado.
3. **Selección abierta**: régimen, ciudad y municipio aceptan valores nuevos
   (listas sugeridas); el tipo de servicio permite marcar los existentes o
   escribir uno nuevo, que queda guardado en el catálogo.
4. **Municipios adicionales (multi-ICA)**: filas que se agregan o quitan en el
   mismo formulario.
5. **Inactivación** con confirmación: el cliente no se elimina, conserva su
   historial.
6. **Permisos (CU002)**: el Administrador y el Contador Senior gestionan; el
   Contador Junior únicamente consulta los clientes asignados a él, incluso si
   intenta entrar por URL directa (404).
7. **Navegación**: la tarjeta del Módulo 1 en el panel principal ya abre el
   listado; los demás módulos siguen marcados como "Próximamente".

### Cómo verificarlo (entorno local)

```bash
cd /home/fredd/documentos/ubuntu/contanika/codigo
source .venv/bin/activate
python gestionar.py runserver
```

1. Entrar a `http://127.0.0.1:8000` e iniciar sesión.
2. Clic en la tarjeta **MOD01 – Gestión de clientes**.
3. Usar **Nuevo cliente**, guardar y verlo en el listado; probar los filtros.
4. Abrir el cliente, **Editar** y **Inactivar** (el registro se conserva).

### Resultado de las pruebas

- 35 pruebas en total: **35 aprobadas** (11 nuevas del Módulo 1).
- Cobertura: **93 %**.
- Pruebas de seguridad incluidas: acceso sin sesión, permisos por rol,
  acceso a cliente ajeno (IDOR), CSRF y validación de NIT duplicado.
- Ruff, bandit y pip-audit sin hallazgos.

### Evidencias a capturar (carpeta `evidencias/01-clientes/`)

1. Listado de clientes con los filtros visibles.
2. Formulario "Nuevo cliente" con municipios y tipos de servicio.
3. Detalle del cliente mostrando servicios y municipios.
4. Cliente inactivado conservado en el listado.

### Pendientes del Módulo 1 (siguientes bloques)

- Importación masiva desde plantilla Excel con resumen de errores.
- Credenciales y accesos a portales: registrar, editar, mostrar/ocultar la
  clave, enmascarado y aviso de más de 90 días sin actualizar.
- Reporte de credenciales (solo en pantalla, sin descarga) para el Administrador.
- Bloquear la edición de credenciales al Contador Junior.

---

## Lunes 21 de septiembre de 2026 — Alineación de la interfaz al prototipo

**Objetivo del bloque:** reemplazar el diseño básico por el del archivo
`contanika-prototipo.html`, para que las capturas de evidencia y los módulos
siguientes nazcan con el diseño definitivo.

### Trabajo realizado

1. **Sistema de diseño** en `estaticos/css/contanika.css`: paleta del
   prototipo (navy `#001524`, teal `#15616D`, naranja `#FF7D00`, verde
   `#0a8a5c`, rojo `#e05252`), tipografías Montserrat + Open Sans e íconos
   Bootstrap Icons.
2. **Estructura base** (`plantillas/base.html`): barra lateral fija de 232 px,
   barra superior con saludo, buscador y avatar, y área de contenido en
   tarjetas; adaptable a celular con botón de menú.
3. **Menú lateral dinámico** (`seguridad/menu.py` y
   `seguridad/context_processors.py`): muestra solo los módulos habilitados
   para el rol (RQF031), marca el módulo activo y señala con "Pronto" los
   módulos aún no construidos.
4. **Inicio de sesión** con el estilo del prototipo (degradado navy→teal,
   tarjeta blanca y logo Contanika).
5. **Panel principal** con franja de indicadores reales (clientes activos,
   inactivos, servicios registrados y usuarios del equipo) y tarjetas de
   módulos.
6. **Reestilo de las tres pantallas de clientes** (listado, formulario y
   detalle) con tablas, insignias, filtros y botones del prototipo.

### Cómo verificarlo (entorno local)

```bash
cd /home/fredd/documentos/ubuntu/contanika/codigo
source .venv/bin/activate
python gestionar.py runserver
```

1. `http://127.0.0.1:8000` → nuevo inicio de sesión.
2. Iniciar sesión → panel con indicadores y tarjetas de módulos.
3. Entrar a **Clientes** → listado con filtros, formulario y detalle nuevos.
4. Reducir el ancho de la ventana → el menú lateral se oculta y aparece el
   botón de menú (diseño adaptable).

### Resultado de las pruebas

- 35 pruebas: **35 aprobadas**. Cobertura: **93 %**.
- Ruff, bandit y pip-audit sin hallazgos.

### Evidencias a capturar (con el diseño nuevo)

- `evidencias/00-inicio/`: login, panel y panel de administración.
- `evidencias/01-clientes/`: listado, formulario, detalle e inactivación.

### Pendientes del Módulo 1 (siguientes bloques)

- Credenciales y accesos a portales (cifrado, mostrar/ocultar, aviso de 90 días)
  y su control por rol.

---

## Lunes 21 de septiembre de 2026 — Módulo 1, bloque 2

**Objetivo del bloque:** importación masiva de clientes desde una plantilla de
Excel con validación fila por fila (RQF013).

### Trabajo realizado

1. **Plantilla Excel descargable** (`clientes/plantilla/`) con los encabezados
   del sistema, una fila de ejemplo y una hoja de instrucciones que explica
   cada columna.
2. **Importación** (`clientes/importar/`): sube el archivo .xlsx, valida cada
   fila (campos obligatorios, tipo de persona, responsable de IVA, NIT sin
   repetir dentro del archivo ni contra el sistema, correo del responsable) e
   importa únicamente las filas válidas.
3. **Resumen en pantalla**: filas leídas, importadas correctamente y con error,
   con el número de fila y el motivo de cada fallo.
4. **Cifrado/seguridad**: se valida la extensión y el tamaño del archivo
   (máximo 5 MB) y los permisos por rol (solo Administrador y Contador Senior).
5. Botones **Plantilla** e **Importar** en el listado de clientes.

### Cómo verificarlo (entorno local)

1. Entrar a **Clientes → Plantilla** y descargar el archivo.
2. Diligenciar una o dos filas y guardar en .xlsx.
3. **Clientes → Importar**, subir el archivo y ver el resumen.
4. Probar con una fila sin NIT para ver el reporte de error.

### Resultado de las pruebas

- 42 pruebas en total: **42 aprobadas** (7 nuevas de importación).
- Cobertura: **92 %**. Ruff, bandit y pip-audit sin hallazgos.
- Casos cubiertos: archivo válido, filas con error, NIT duplicado, extensión
  inválida y permisos del Contador Junior.

### Evidencias a capturar (carpeta `evidencias/01-clientes/`)

1. Plantilla de Excel descargada.
2. Pantalla de importación con el resumen de importados y errores.

---

## Martes 22 de septiembre de 2026 — Módulo 1, bloque 3: credenciales y accesos a portales

**Objetivo del bloque:** completar la gestión de credenciales de acceso a
portales del cliente (DIAN, Hacienda, firma electrónica, etc.) con cifrado,
enmascarado, aviso de 90 días y control por rol.

### Trabajo realizado

1. **CRUD de credenciales** desde el detalle del cliente: crear, editar y
   eliminar credenciales mediante modal AJAX.
2. **Cifrado/descifrado** con Fernet: la contraseña se guarda cifrada en
   `clave_cifrada` y solo se descifra temporalmente al mostrarla en pantalla.
3. **Enmascarado y botón mostrar/ocultar**: la contraseña se muestra en un
   campo tipo `password` con un botón para revelarla u ocultarla.
4. **Aviso de 90 días**: credenciales con más de 90 días sin actualizar
   muestran advertencia visual en la tabla y en el reporte.
5. **Control por rol**: Administrador y Contador Senior gestionan credenciales;
   el Contador Junior solo puede ver las de los clientes que tiene asignados.
6. **Reporte de credenciales** en pantalla (sin descarga), accesible desde el
   detalle del cliente.
7. **Configuración robusta**: `.env.example` documenta la variable
   `CREDENCIAL_CLAVE_CIFRADO` y las pruebas usan una clave fija independiente
   del entorno.
8. **Ajuste de paginación del listado**: el default pasó de 25 a 10 clientes
   por página.

### Cómo verificarlo (entorno local)

1. Entrar a **Clientes**, abrir un cliente y desplazarse al panel
   **Credenciales y accesos a portales**.
2. Clic en **Agregar credencial**, guardar y verla enmascarada en la tabla.
3. Clic en el ojo para revelar la contraseña.
4. Clic en **Ver reporte** para abrir el reporte de credenciales.
5. Probar con una credencial cuya `fecha_ultima_actualizacion` tenga más de
   90 días para ver el aviso.
6. Ingresar como Contador Junior: solo debe ver credenciales de sus clientes
   asignados y no debe tener botones de agregar/editar/eliminar.

### Resultado de las pruebas

- 70 pruebas en total: **70 aprobadas** (1 nueva de paginación).
- Cobertura: **91 %**. Ruff, bandit y pip-audit sin hallazgos.

### Evidencias a capturar (carpeta `evidencias/01-clientes/`)

1. Detalle del cliente con credenciales enmascaradas.
2. Modal de creación/edición de credencial.
3. Reporte de credenciales con aviso de 90 días.
4. Vista del Contador Junior sin botones de edición.

### Pendientes del Módulo 1

- Ninguno. Módulo 1 completado.
