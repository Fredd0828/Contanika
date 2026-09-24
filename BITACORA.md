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

---

## Miércoles 23 de septiembre de 2026 — Módulo 2, bloque 1: calendario, tabla DIAN y cálculo de vencimientos

**Objetivo del bloque:** dejar navegable el calendario con vistas día/semana/mes,
la tabla de referencia DIAN 2026 cargada (manual y masiva) y el cálculo
automático de vencimientos por cliente según NIT/cédula y régimen.

### Trabajo realizado

1. **Tabla de referencia DIAN 2026** (`aplicaciones/calendario/datos_dian_2026.py`):
   440 registros oficiales extraídos del PDF del calendario tributario 2026
   (IVA bimestral y cuatrimestral, retención mensual, renta personas jurídicas,
   grandes contribuyentes, renta personas naturales y RST).
2. **Comando de carga** `cargar_calendario_dian_2026`: idempotente, crea o
   actualiza por obligación + grupo + período.
3. **Reglas de grupo DIAN** (`servicios.calcular_grupo_nit`): empresas por
   último dígito del NIT, personas naturales por los dos últimos dígitos de la
   cédula; documentos extranjeros quedan para registro manual.
4. **Obligaciones por régimen** (`servicios.obligaciones_por_cliente`):
   régimen simple (cualquier variante del nombre) → RST; jurídica ordinaria →
   renta PJ + retención (+ IVA si es responsable); natural → renta PN
   (+ IVA y retención si es responsable).
5. **Cálculo automático** (`generar_vencimientos_cliente` y masivo): crea
   vencimientos nacionales "Pendiente de validar" sin duplicar; omite clientes
   inactivos y extranjeros.
6. **Calendario navegable** en vistas día/semana/mes con grilla renderizada en
   el servidor (sin librerías JS pesadas), filtros desplegables, leyenda por
   ámbito/estado y navegación entre períodos.
7. **Listado de vencimientos** con filtros por fecha, cliente, ámbito, estado,
   tipo y responsable, con paginación.
8. **CRUD de vencimientos manuales** (distritales/municipales), cambio de
   estado de presentación y validación de los automáticos DIAN.
9. **Carga DIAN** manual (una fila) y masiva (Excel con plantilla descargable
   y resumen de errores), exclusiva del Administrador.
10. **Alertas por vencimiento** (días de anticipación y canal) y **anotaciones
    libres** con visibilidad privada/equipo/rol/etiqueta.
11. **Permisos**: Junior solo consulta vencimientos de sus clientes asignados
    (lista, detalle y calendario); no crea, edita, valida ni configura alertas.
12. **Integración**: rutas registradas, tarjeta del panel y menú lateral
    activos para el Módulo 2; `AGENTS.md` creado con el contexto del proyecto.

### Cómo verificarlo (entorno local)

```bash
cd /home/fredd/documentos/ubuntu/contanika/codigo
source .venv/bin/activate
python gestionar.py cargar_calendario_dian_2026
python gestionar.py runserver
```

1. Entrar a `http://127.0.0.1:8000` e iniciar sesión.
2. Clic en **Calendario** del menú lateral: vista mensual con vencimientos.
3. Probar las vistas **Día/Semana/Mes**, la navegación y los filtros.
4. **Lista** → botón **Calcular vencimientos DIAN** (crea los de los clientes).
5. Abrir un vencimiento: cambiar estado, validar y agregar una alerta.
6. **Tabla DIAN** (solo Administrador): carga manual y plantilla Excel.
7. Ingresar como Contador Junior: solo ve vencimientos de sus clientes.

### Resultado de las pruebas

- 156 pruebas en total: **156 aprobadas** (86 nuevas del Módulo 2).
- Cobertura total: **92 %**; módulo calendario: servicios 99 %, formularios
  99 %, importación 98 %, selectores 92 %, vistas 89 %.
- Pruebas de seguridad: acceso sin sesión, módulo inhabilitado (403), IDOR de
  vencimientos ajenos (404), permisos por rol, CSRF y XSS en anotaciones.
- Ruff (estilo y formato), bandit y pip-audit sin hallazgos.

### Evidencias

- `evidencias/02-calendario/` (HTML renderizado del calendario mes/semana/día,
  lista de vencimientos y carga DIAN).
- `scripts/bd/02_datos_iniciales.sql` actualizado con los 440 registros DIAN.

### Pendientes del Módulo 2 (siguientes bloques)

- Vencimientos originados en tareas del Kanban (cuando se construya el Módulo 3).
- Envío real de alertas (management command `enviar_alertas` + cron, decisión T3).
- Calendario individual por cliente desde el perfil del cliente (Módulo 1).

---

## Miércoles 23 de septiembre de 2026 — Módulo 2, bloque 2: legibilidad del calendario y vencimientos en el perfil del cliente

**Objetivo del bloque:** mejorar la legibilidad visual del calendario (eventos
más grandes y grilla más marcada) y llevar los vencimientos al perfil del
cliente, donde se pueden ver, calcular y registrar.

### Trabajo realizado

1. **Rediseño visual del calendario** (`estaticos/css/contanika.css`):
   - Eventos más grandes (11.5 px, mayor relleno y borde de 4 px) con sombra
     suave y realce al pasar el mouse.
   - Grilla con líneas más gruesas (separación y borde de 2 px), encabezados
     de días en navy, celdas más altas (132 px) y día actual con marco teal
     de 3 px; diseño responsive conservado.
2. **Vencimientos en el perfil del cliente** (`clientes/vencimientos_panel.html`):
   tabla con fecha, obligación, ámbito, municipio, estado de presentación y
   validación, con acceso al detalle de cada vencimiento.
3. **Acciones desde el perfil**: botón **Calcular vencimientos DIAN** (solo de
   ese cliente, con aviso si es extranjero sin grupo calculable) y botón
   **Agregar vencimiento** que abre el formulario con el cliente
   preseleccionado (`?cliente=pk`).
4. **Enlace "Ver en la lista"** con el filtro del cliente ya aplicado.
5. El Contador Junior ve el panel solo con los vencimientos de sus clientes
   asignados y sin botones de acción (mismo criterio del Módulo 1).

### Cómo verificarlo (entorno local)

1. Entrar a **Calendario**: los eventos se ven más grandes y la grilla más
   marcada; probar las vistas día/semana/mes.
2. Entrar a **Clientes** y abrir un cliente: aparece el panel
   **Vencimientos del cliente** debajo de la ficha.
3. Clic en **Calcular vencimientos DIAN**: se generan solo los de ese cliente.
4. Clic en **Agregar vencimiento**: el formulario llega con el cliente elegido.
5. Con un cliente extranjero (pasaporte/CE), el cálculo muestra el aviso de
   registro manual.

### Resultado de las pruebas

- 161 pruebas en total: **161 aprobadas** (5 nuevas: panel en el perfil,
  cálculo individual, cliente extranjero, Junior sin permiso y cliente
  preseleccionado).
- Cobertura total: **93 %**; `calendario/servicios.py` 99 %,
  `calendario/vistas.py` 90 %.
- Ruff (estilo y formato), bandit y pip-audit sin hallazgos.

### Evidencias

- `evidencias/02-calendario/calendario_mes.html` actualizado con el nuevo estilo.
- `evidencias/02-calendario/perfil_cliente_vencimientos.html` (panel en la ficha).

### Pendientes del Módulo 2

- Vencimientos originados en tareas del Kanban (cuando se construya el Módulo 3).
- Envío real de alertas (management command `enviar_alertas` + cron, decisión T3).

---

## Miércoles 23 de septiembre de 2026 — Módulo 3, bloque 1: tablero Kanban, historial, observaciones y calendario

**Objetivo del bloque:** dejar navegable el tablero de tareas (CU y HU007-009,
041, 052): tarjetas por cliente con historial de cambios y observaciones de
avance, permisos por rol, notificación al responsable e integración con el
Módulo 2 (vencimientos originados en tareas marcadas para el calendario).

### Trabajo realizado

1. **Tablero Kanban** (`plantillas/tareas/tablero.html`): columnas Por hacer /
   En progreso / En revisión / Terminado, tarjetas ordenadas por prioridad y
   fecha más próxima, arrastrar y soltar para cambiar de estado (con reversión
   automática si el servidor rechaza el cambio) y filtros desplegables por
   cliente, responsable, prioridad y tipo de tarea (selección abierta).
2. **Tarjeta expandida** (modal AJAX, con página completa como respaldo sin
   JavaScript): edición completa para Administrador y Contador Senior; el
   Contador Junior solo cambia el estado y agrega observaciones de sus propias
   tareas. Incluye historial de cambios (usuario y fecha), observaciones de
   avance y acceso directo al expediente del cliente (Módulo 1).
3. **Permisos (especificación del Módulo 3)**: Administrador y Contador Senior
   crean, editan y eliminan cualquier tarea; el Contador Junior únicamente
   actualiza el estado y las observaciones de las tareas asignadas a él (IDOR
   probado: 404 al intentar acceder a tareas ajenas por URL directa).
4. **Notificación al responsable al cambiar de estado**: sin tabla nueva en el
   diccionario de datos (decisión de sesión); se calcula a partir de
   `historial_tarea` (cambios de los últimos 7 días hechos por otra persona) y
   se expone en un endpoint AJAX (`tareas:notificaciones`) que alimenta la
   campana de notificaciones del tablero.
5. **Integración con el Calendario (Módulo 2)**: casilla "mostrar en
   calendario" al crear o editar la tarea; si está activa, se crea o actualiza
   un `Vencimiento` con `tarea` asociada (misma fecha, cliente y responsable);
   se elimina si se desmarca o la tarea se borra. El estado de presentación
   sigue el estado de la tarea (Terminado → Presentada). El calendario ahora
   distingue el origen (tributario / tarea) con un nuevo filtro "Origen",
   color propio en la grilla y leyenda, y un enlace "Ver tarea" en el detalle
   del vencimiento en vez de la edición manual. No se modificó el modelo de
   datos de ninguno de los dos módulos (el campo `tarea` en `Vencimiento` ya
   existía desde el Módulo 2).
6. **Integración**: rutas registradas, tarjeta del panel principal y menú
   lateral activos para el Módulo 3.

### Cómo verificarlo (entorno local)

```bash
cd /home/fredd/documentos/ubuntu/contanika/codigo
source .venv/bin/activate
python gestionar.py runserver
```

1. Entrar a **Tareas** en el menú lateral: tablero con las cuatro columnas.
2. **Nueva tarea**: crear una tarjeta con cliente, título, responsable,
   prioridad y fecha de vencimiento; marcar "Mostrar también en el Calendario"
   y verificar que aparece en **Calendario** con el color de "Tarea" y el
   filtro de Origen.
3. Arrastrar una tarjeta a otra columna: el cambio se guarda solo y el
   historial de la tarjeta lo registra.
4. Abrir una tarjeta, agregar una observación y revisar el historial.
5. Clic en **Ver expediente completo del cliente** desde la tarjeta.
6. Ingresar como Contador Junior: solo ve sus tareas asignadas, no tiene
   botones de crear/editar/eliminar y solo puede cambiar el estado y comentar
   sus propias tarjetas (una URL directa a una tarea ajena da 404).
7. Revisar la campana de notificaciones tras cambiar el estado de una tarea
   asignada a otro usuario (con esa sesión).

### Resultado de las pruebas

- 212 pruebas en total: **212 aprobadas** (53 nuevas del Módulo 3, más los
  ajustes de filtro "Origen" del Módulo 2).
- Cobertura total: **92 %**; módulo tareas: formularios y servicios 100 %,
  modelos 97 %, selectores 94 %, vistas 82 %.
- Pruebas de seguridad: acceso sin sesión, módulo inhabilitado (403), permisos
  por rol (403 para el Junior en crear/editar/eliminar), IDOR de tareas ajenas
  (404 en detalle, cambiar estado y observaciones), CSRF y XSS en el título de
  la tarjeta.
- Ruff (estilo y formato), bandit y pip-audit sin hallazgos.

### Evidencias

- `evidencias/03-tareas/` (tablero Kanban, tarjeta expandida con historial,
  vista del Contador Junior, integración con el calendario).

### Pendientes del Módulo 3 (siguientes bloques)

- Notificación por correo/WhatsApp al cambiar de estado (por ahora solo
  notificación interna calculada desde el historial; el envío real queda con
  la decisión T3 de alertas automáticas).
- Reporte de tareas (individual o total) del Módulo 10.
- Panel de tareas del cliente en su ficha (Módulo 1), como el de vencimientos.
