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

---

## Jueves 24 de septiembre de 2026 — Módulo 4, bloque 1: expedición de documentos y certificados

**Objetivo del bloque:** dejar navegable el Módulo 4 (HU010-012, 042): catálogo
de las 6 plantillas base con texto y campos reales, gestión de plantillas
(Administrador), panel de generación con campos dinámicos por tipo de
documento (simples y repetibles), firma del contador y generación real del
PDF con ReportLab, histórico filtrable y descarga individual.

### Trabajo realizado

1. **Modelos**: `Documento.archivo_url` (URLField sin uso real) se cambió a
   `archivo` (`FileField`) y se agregó `periodo`; `Usuario.firma_url` se
   cambió a `firma` (`ImageField`) y se agregó `identificacion`, para poder
   cumplir el requisito de "cargar la imagen de firma" — ningún modelo del
   proyecto usaba hasta ahora un campo de archivo real, todos eran `URLField`
   sin mecanismo de subida (mismo diagnóstico que el plan pendiente de
   adjuntos en Expediente, Módulo 9, que sigue sin construirse).
2. **Catálogo de plantillas**: las 6 plantillas base (ya existían solo con el
   nombre) se completaron con texto predeterminado (sintaxis de plantillas de
   Django, con marcadores `{{ cliente }}`, `{{ periodo }}`, etc.) y sus campos
   propios simples o repetibles (por ejemplo, nombre y porcentaje de cada
   accionista en el certificado de composición accionaria), sembrados de forma
   idempotente por `cargar_datos_iniciales` (el texto solo se fija al crear la
   plantilla, para no pisar ediciones del Administrador en corridas futuras).
   Gestión de plantillas (crear, editar texto y campos) solo para
   Administrador.
3. **Firma del contador**: vista "Mi firma" (Administrador y Contador Senior)
   para cargar o reemplazar la imagen de firma, identificación y tarjeta
   profesional; el panel de generación permite elegir cuál firma guardada usar
   entre los usuarios que ya la tienen cargada.
4. **Panel de generación** en dos pasos: el formulario común (cliente,
   plantilla, período, descripción, firma) se combina con los campos propios
   de la plantilla elegida, cargados por AJAX sin recargar la página; las
   filas repetibles se agregan o quitan con JavaScript sencillo (mismo
   espíritu que los municipios adicionales del Módulo 1). Los datos validados
   se guardan en la sesión para la previsualización; al confirmar se
   re-validan contra las consultas visibles del usuario (nunca se confía en
   ids sueltos) y se genera el `Documento` con sus valores, detalles y el PDF,
   todo en una transacción.
5. **PDF con ReportLab** (Platypus): encabezado del despacho, cuerpo del
   certificado ya interpolado (con el mismo escape de Django usado en la
   previsualización, para que ningún valor capturado pueda inyectar marcado),
   bloque de firma con la imagen, nombre, identificación y tarjeta profesional
   del contador elegido.
6. **Histórico y panel del cliente**: listado filtrable por tipo de documento
   y rango de fechas, descarga individual del PDF (excepción expresa a la
   regla de centralización de descargas: el certificado individual sí se
   descarga desde aquí, por los tres roles), eliminación solo para
   Administrador o Contador Senior. Nueva pestaña "Documentos" en la ficha del
   cliente con los últimos documentos generados.
7. **Integración**: rutas registradas, `config/urls.py` ahora sirve `media/`
   en desarrollo (faltaba, necesario para servir firmas y PDFs reales), menú
   lateral y tarjeta del panel principal activos para el Módulo 4.

### Cómo verificarlo (entorno local)

```bash
cd /home/fredd/documentos/ubuntu/contanika/codigo
source .venv/bin/activate
python gestionar.py runserver
```

1. Entrar a **Documentos** en el menú lateral: histórico vacío.
2. Como Administrador, entrar a **Gestión de plantillas**: las 6 base ya
   tienen texto predeterminado; editar el texto de una; crear una plantilla
   nueva (la séptima, aún sin definir en el spec) con un campo propio.
3. **Mi firma**: cargar una imagen, identificación y tarjeta profesional.
4. Desde la ficha de un cliente → pestaña **Documentos** → "Generar
   documento": elegir "Certificado de composición accionaria", ver que el
   formulario cambia por AJAX a sus campos propios, agregar dos accionistas
   sin recargar la página, previsualizar (texto ya interpolado) y confirmar:
   el PDF se genera y el detalle del documento queda disponible.
5. Descargar el PDF y confirmar encabezado, cuerpo y bloque de firma.
6. Filtrar el histórico por tipo de documento y por rango de fechas.
7. Como Contador Junior: solo genera/ve documentos de sus clientes asignados
   (404 en URL directa a un documento ajeno); sin acceso a Gestión de
   plantillas ni Mi firma (403); sin botón eliminar. Como Contador Senior, sí
   puede eliminar un documento generado por otro usuario.

### Resultado de las pruebas

- 278 pruebas en total: **278 aprobadas** (56 nuevas del Módulo 4).
- Cobertura total: **92 %**; módulo documentos: formularios y selectores
  100 %, modelos 99 %, servicios 95 %, vistas 80 %.
- Pruebas de seguridad: acceso sin sesión, módulo inhabilitado (403), permisos
  por rol (403 para Junior en plantillas/mi firma/eliminar, para Senior en
  plantillas), IDOR de documentos ajenos (404 en detalle y descarga), CSRF y
  XSS en la descripción del documento (verificado también en vivo contra el
  servidor de desarrollo, no solo en pruebas automatizadas).
- Ruff (estilo y formato) y bandit sin hallazgos — una excepción justificada
  (`# nosec`) en `documentos/selectores.py::renderizar_texto`: el `mark_safe`
  solo envuelve texto que ya pasó por el autoescape de Django, con el texto
  literal editable únicamente por el Administrador.
- pip-audit sin vulnerabilidades.
- Verificación adicional en vivo (no solo pruebas automatizadas): contra el
  servidor de desarrollo ya corriendo, con sesión real de Administrador, se
  ejecutó el flujo completo por HTTP (login, subir firma, generar el
  certificado de composición accionaria con dos accionistas, previsualizar
  con intento de XSS en la descripción, confirmar, descargar el PDF real
  —1 página, cabeceras `Content-Type`/`Content-Disposition` correctas— y
  confirmar la pestaña Documentos en la ficha del cliente). No se usó un
  navegador real (sin acceso interactivo en este entorno); si se requiere
  evidencia visual para el documento Word, conviene repetir el flujo en un
  navegador y capturar las pantallas.

### Pendientes del Módulo 4 (siguientes bloques)

- Séptima plantilla: nombre, campos y texto predeterminado (spec explícito:
  "falta definir", no se inventó en este bloque).
- Reporte específico no aplica (no está en el alcance del Módulo 10 según el
  spec vigente); confirmar si eso sigue así al cerrar el Módulo 10.
- `ConfiguracionDespacho.membrete_url` sigue sin usarse (el PDF imprime el
  nombre y ciudad del despacho como texto, no como imagen) — evaluar si vale
  la pena resolverlo junto con el plan pendiente de adjuntos (Módulo 9), que
  tiene el mismo diagnóstico de "URLField sin mecanismo de subida real".
  **Resuelto** en el bloque de cierre de pendientes (vista Datos del despacho).

---

## Jueves 24 de septiembre de 2026 — Módulo 5, bloque 1: hallazgos y revisiones

**Objetivo del bloque:** dejar navegable el Módulo 5 (HU016-018): registro y
edición de hallazgos por cliente (tipo abierto, período revisado,
responsable, prioridad, descripción, adjuntos de soporte), cambio de estado
con observación obligatoria al cerrar, listado filtrable, y pestaña
"Hallazgos" en la ficha del cliente.

### Trabajo realizado

1. **Modelo**: `Hallazgo` ya existía completo y coincide exactamente con el
   spec (tipo, período, responsable, prioridad, descripción, estado,
   observación de cierre); no se modificó.
2. **Adjuntos de soporte**: `comunes.Adjunto.archivo_url` (URLField sin uso
   real, mismo diagnóstico ya resuelto en el Módulo 4 para
   `Documento`/`Usuario.firma`) se cambió a `archivo` (`FileField`). Al ser
   `Adjunto` una tabla genérica sin FK real hacia `Hallazgo`
   (`tabla_origen`/`id_origen`), `eliminar_hallazgo` borra a mano el archivo
   físico y la fila de cada adjunto antes de borrar el hallazgo. Sin
   patrón de subida múltiple en el proyecto, los adjuntos se suben de uno en
   uno desde el detalle del hallazgo (extensión y tamaño validados: PDF,
   Word, Excel o imagen, máximo 10 MB), cada uno con su propio botón de
   descarga y eliminación.
3. **Permisos**: el spec no los detalla para este módulo (a diferencia de
   Tareas y Documentos); se decidió con el usuario seguir el patrón de
   Documentos/Calendario — Contador Junior gestiona (crea, edita, cambia
   estado, adjunta) solo los hallazgos de sus clientes asignados, sin
   eliminar; Administrador y Contador Senior gestionan cualquiera, incluida
   la eliminación.
4. **Cambio de estado**: un solo formulario (estado + observación de
   cierre) que exige la observación únicamente al pasar a "Cerrado" y
   reutiliza `Hallazgo.cerrar()`, ya existente en el modelo.
5. **Listado y panel**: histórico filtrable por tipo (campo abierto, con
   `datalist` de tipos ya usados), estado, responsable y rango de fechas del
   período revisado; pestaña "Hallazgos" nueva en la ficha del cliente con
   los últimos registrados y acceso directo a registrar uno nuevo.
6. **Integración**: rutas registradas, menú lateral y tarjeta del panel
   principal activos para el Módulo 5. Sin CSS nuevo: se reutilizan
   `.badge-est` (estado) y `.kb-prio` (prioridad), ya usados en Calendario y
   Tareas con los mismos valores.

### Cómo verificarlo (entorno local)

```bash
cd /home/fredd/documentos/ubuntu/contanika/codigo
source .venv/bin/activate
python gestionar.py migrate
python gestionar.py runserver
```

1. Entrar a **Hallazgos** en el menú lateral: listado vacío.
2. Desde la ficha de un cliente → pestaña **Hallazgos** → "Registrar
   hallazgo": tipo con datalist, rango de fechas del período, responsable,
   prioridad, descripción → guardar → aparece en el panel y en el listado.
3. Entrar al detalle: adjuntar un PDF y una imagen, descargar cada uno,
   eliminar uno.
4. Cambiar el estado a "Cerrado" sin observación (debe rechazarlo) y con
   observación (debe cerrarlo y mostrar la observación en el detalle).
5. Filtrar el listado por tipo, estado, responsable y rango de fechas.
6. Como Contador Junior: solo ve/gestiona hallazgos de sus clientes
   asignados (404 en URL directa a uno ajeno, incluida la descarga de su
   adjunto); sin botón eliminar. Como Contador Senior, sí puede eliminar un
   hallazgo de otro usuario (y sus adjuntos desaparecen del disco).

### Resultado de las pruebas

- 327 pruebas en total: **327 aprobadas** (49 nuevas del Módulo 5).
- Cobertura total: **93 %**; módulo hallazgos: modelos, selectores,
  servicios y formularios 100 %, vistas 95 %.
- Pruebas de seguridad: acceso sin sesión, módulo inhabilitado (403),
  permisos por rol (403 al eliminar para Junior), IDOR de hallazgos y
  adjuntos ajenos (404 en detalle, edición, descarga y agregar adjunto),
  CSRF y XSS en la descripción se escapan en el detalle.
- Ruff (estilo y formato), bandit y pip-audit sin hallazgos.

### Pendientes del Módulo 5 (siguientes bloques)

- Sin reporte propio en el Módulo 10 (confirmado explícitamente en el spec).
- El filtro de rango de fechas compara solo contra `fecha_inicio_periodo`
  (no modela traslape con `fecha_fin_periodo`), igual de simple que el resto
  de filtros de fecha del proyecto — revisar si algún caso real lo necesita.
  **Resuelto** en el bloque de cierre de pendientes (filtro por traslape).

---

## Jueves 24 de septiembre de 2026 — Cierre de pendientes de los Módulos 4 y 5

**Objetivo del bloque:** resolver los pendientes que quedaron abiertos en los
Módulos 4 y 5 antes de arrancar el Módulo 6.

### Trabajo realizado

1. **Membrete del despacho (M4)**: `ConfiguracionDespacho.membrete_url`
   (URLField sin uso) se cambió a `membrete` (`ImageField`). Nueva vista
   **Datos del despacho** (solo Administrador), enlazada desde el histórico
   de documentos, para editar nombre, NIT, ciudad, dirección, teléfono,
   correo y cargar la imagen del membrete (máximo 2 MB). El encabezado de
   los PDF usa la imagen escalada sin deformarla al ancho útil de la página
   (alto máximo 3 cm); si no hay membrete, se conserva el nombre y la ciudad
   como texto. La función `encabezado_despacho()` queda lista para que el
   Módulo 6 la reutilice en la cuenta de cobro.
2. **Enlace de Gestión de plantillas**: se mostraba también al Contador
   Senior (que recibía 403 al entrar); ahora el histórico solo muestra
   "Gestión de plantillas" y "Datos del despacho" al Administrador.
3. **Séptima plantilla (M4)**: se decidió con el usuario no sembrarla hasta
   que se defina; el Administrador ya puede crearla desde "Gestión de
   plantillas" sin cambios de código.
4. **Filtro de hallazgos por traslape (M5)**: el rango de fechas del listado
   ahora encuentra un hallazgo si su período revisado se cruza con el rango
   consultado (antes solo comparaba la fecha de inicio). Ejemplo: un
   hallazgo de enero a junio aparece al filtrar solo marzo.
5. Scripts SQL (`01_esquema_contanika.sql`, `02_datos_iniciales.sql`)
   actualizados con la columna `membrete`.

### Cómo verificarlo (entorno local)

```bash
cd /home/fredd/documentos/ubuntu/contanika/codigo
source .venv/bin/activate
python gestionar.py migrate
python gestionar.py runserver
```

1. Como Administrador: **Documentos** → **Datos del despacho** → cargar una
   imagen de membrete y guardar; la vista previa aparece arriba.
2. Generar un documento y descargar el PDF: el encabezado es la imagen.
3. Como Contador Senior: el histórico ya no muestra "Gestión de plantillas"
   ni "Datos del despacho" (403 por URL directa).
4. **Hallazgos**: registrar uno con período de enero a junio y filtrar el
   listado solo por marzo: debe aparecer.

### Resultado de las pruebas

- 335 pruebas en total: **335 aprobadas** (8 nuevas).
- Cobertura total: **93 %**; documentos/servicios 96 %, hallazgos/selectores 100 %.
- Ruff (estilo y formato), bandit y pip-audit sin hallazgos.

### Pendientes

- Séptima plantilla del Módulo 4: pendiente de definición por parte del
  usuario (se crea desde la interfaz, no requiere código).
- Al reemplazar el membrete, la imagen anterior queda en `media/despacho/`
  (mismo comportamiento que la firma del Módulo 4).

---

## Jueves 24 de septiembre de 2026 — Módulo 6, bloque 1: honorarios, catálogos y cuentas de cobro

**Objetivo del bloque:** dejar navegable la parte de facturación del Módulo 6
(HU044, HU049 y la generación de la cuenta de cobro de HU016): honorario por
cliente, catálogos, cuenta de cobro con líneas de servicio y PDF con membrete.
Abonos y cartera (bloque 2) y envíos (bloque 3) quedan para los siguientes.

### Trabajo realizado

1. **Modelos** (decisiones con el usuario):
   - Tabla nueva `honorario_servicio`: monto por tipo de servicio cuando el
     honorario es "Por servicio" (HU044, criterio 2). El modelo pasa a tener
     **37 tablas**; hay que reflejarlo en el diccionario de datos del Word.
   - `Honorario` ganó `usuario_actualizacion` y `fecha_actualizacion`
     (HU044, criterio 4).
   - `CuentaCobro.archivo_url` (URLField sin uso) → `archivo` (`FileField`), y
     se agregaron `fecha_inicio_periodo`/`fecha_fin_periodo`.
2. **Honorario del cliente**: nueva pestaña **Honorarios** en la ficha del
   cliente con el tipo, el monto (o el detalle por servicio) y el último
   cambio (fecha y usuario). El Administrador lo configura: fijo mensual con
   un monto, o por servicio con un monto por cada tipo de servicio del
   cliente. Cambiar el honorario no altera las cuentas ya generadas.
3. **Catálogos** (solo Administrador): conceptos facturables, cuentas
   bancarias del despacho y métodos de pago en una sola pantalla, con crear,
   editar y eliminar; no se elimina un elemento ya usado en cuentas o abonos.
4. **Generar cuenta de cobro** (solo Administrador): al elegir el cliente se
   sugieren el valor total (según su honorario) y una línea por cada servicio
   (con su monto si el honorario es por servicio). Las líneas se agregan,
   quitan y reordenan; cada una puede tomar un concepto del catálogo, que
   completa la descripción y el valor sugerido. Si se indican valores por
   línea, la suma debe ser igual al total (HU049). El fin del período se
   calcula solo (mensual a anual); el personalizado pide ambas fechas.
5. **PDF de la cuenta de cobro** (ReportLab): membrete del despacho (reutiliza
   el encabezado del Módulo 4, movido a `comunes/pdf.py`), número, ciudad y
   fecha, cliente con su documento, "debe a" el despacho con su NIT, valor,
   tabla de líneas con total, período, fecha de vencimiento, método de pago y
   datos bancarios. Todo texto capturado se escapa antes de pasar a ReportLab.
6. **Histórico** en el menú **Honorarios**: filtrable por cliente, estado de
   pago, período y fecha de generación; detalle, descarga individual del PDF
   (excepción expresa a la regla de descargas centralizadas) y eliminación
   solo para Administrador y solo si la cuenta no tiene abonos.
7. **Visibilidad**: Contador Senior y Contador Junior solo consultan las
   cuentas de sus clientes asignados (404 en URL directa a una ajena).
8. La ficha del cliente ahora abre la pestaña indicada en la URL
   (`#tab-honorarios`), para volver a ella después de configurar el honorario.

### Cómo verificarlo (entorno local)

```bash
cd /home/fredd/documentos/ubuntu/contanika/codigo
source .venv/bin/activate
python gestionar.py migrate
python gestionar.py runserver
```

1. **Honorarios → Catálogos**: agregar una cuenta bancaria (ej. Bancolombia,
   Ahorros) y revisar los conceptos y métodos de pago sembrados.
2. Ficha de un cliente con servicios → pestaña **Honorarios** → "Configurar
   honorario": elegir "Por servicio", poner montos y guardar; debe mostrar el
   total y el último cambio.
3. "Generar cuenta de cobro": revisar que vengan las líneas y el valor;
   subir/bajar una línea, agregar una con un concepto del catálogo, cuadrar la
   suma y generar. Probar también con una suma que no cuadre (debe rechazarla).
4. Descargar el PDF y **revisarlo visualmente** (membrete, tabla de líneas,
   datos bancarios): en este entorno no se pudo renderizar el PDF a imagen.
5. Como Contador Senior o Junior: sin botones de generar, catálogos ni
   eliminar (403 por URL directa); solo ven cuentas de sus clientes.

### Resultado de las pruebas

- 404 pruebas en total: **404 aprobadas**; la carpeta `pruebas/finanzas`
  suma 73 (casos parametrizados incluidos).
- Cobertura total: **94 %**; finanzas: selectores 100 %, servicios 99 %,
  formularios 99 %, vistas 99 %.
- Pruebas de seguridad: acceso sin sesión, módulo inhabilitado (403),
  permisos por rol (403 para Senior/Junior en generar, catálogos, honorario y
  eliminar), IDOR en detalle y descarga (404), CSRF (403 sin token) y XSS en
  las líneas de servicio (escapado en el detalle y en el PDF).
- Ruff (estilo y formato), bandit y pip-audit sin hallazgos.

### Pendientes del Módulo 6

- Registro de abonos con disparador (trigger) en PostgreSQL para saldo
  anterior/resultante y estado de pago, panel de cartera con días de mora
  (rojo a más de 30 días) e historial de abonos en la ficha (HU016 parte 2,
  HU017, HU018).
- Envío individual y masivo de cuentas de cobro, recordatorios de pago y
  registro en Comunicaciones (HU045-HU047).
- Actualizar el diccionario de datos del Word: tabla `honorario_servicio` y
  columnas nuevas de `honorario` y `cuenta_cobro`.
- Nota de alcance: HU015 dice que el Contador Junior no crea ni edita
  hallazgos, pero en el Módulo 5 se decidió que sí puede (sobre sus clientes).
  **Resuelto el 25-sep-2026:** el usuario confirmó mantener el criterio
  implementado (el Junior gestiona los hallazgos de sus clientes, sin
  eliminar); queda como decisión que modifica la HU015 en el documento Word.

> **Reordenado el 25-sep-2026:** a pedido del usuario, los envíos pasan a ser
> el Bloque 2 (con la ampliación de programación y cobro automático) y los
> abonos con disparador y la cartera, el Bloque 3.

---

## Viernes 25 de septiembre de 2026 — Módulo 6, bloque 2: envíos, recordatorios y cobro automático

**Objetivo del bloque:** que las cuentas de cobro y los recordatorios de pago
se puedan enviar por correo y WhatsApp, uno por uno o de forma masiva, ahora o
programados (HU045, HU046, HU047), y además — **ampliación de alcance pedida
por el usuario** — el cobro mensual automático y los recordatorios automáticos.

### Decisiones con el usuario

- **WhatsApp por enlace `wa.me`** (gratis, sin trámites con Meta). Como exige
  que una persona pulse "Enviar", los WhatsApp programados o masivos quedan en
  una **bandeja de pendientes**. La API oficial queda como mejora futura.
- **Correo: se configura después.** Mientras `CORREO_HOST` esté vacío en `.env`,
  los correos se muestran en la consola de `runserver`.
- **Programar las tres cosas:** envíos en fecha y hora, cobro mensual
  automático y recordatorios automáticos.

### Trabajo realizado

1. **Modelos** (migración `finanzas 0003`, el modelo pasa a **39 tablas**):
   `configuracion_cobro` (una fila con los parámetros del cobro mensual y de
   los recordatorios) y `envio_programado` (cada envío: tipo, canal, fecha,
   estado, usuario, comunicación registrada, error).
2. **Canales** (`finanzas/envios.py`): correo con el PDF adjunto; WhatsApp con
   el mensaje ya escrito (saldo, vencimiento, datos bancarios) y un **enlace
   seguro y temporal al PDF** (firmado, vence en 30 días, no se puede adivinar
   el de otra cuenta). El celular se toma del contacto del cliente (celular
   colombiano de 10 dígitos → se antepone 57).
3. **Detalle de la cuenta**: panel "Enviar al cliente" (cuenta de cobro o
   recordatorio; correo, WhatsApp o ambos; ahora o programado) e **historial de
   envíos** con «Abrir WhatsApp», «Reintentar» (fallidos) y cancelar.
4. **Envío masivo** (HU046, HU047): selección de cuentas (o "seleccionar
   todas"), canal y momento → **confirmación del listado** → **resumen** de
   enviados, fallidos, WhatsApp por abrir y programados, con el detalle de
   cada caso. Recordatorios: solo cuentas con saldo pendiente.
5. **Bandeja de WhatsApp pendientes**, **Envíos programados** (filtro por
   estado, cancelar) y **Cobro automático** (configuración + «Ejecutar ahora»),
   con accesos desde la pantalla de Honorarios (la bandeja muestra contador).
6. **Proceso automático** `python gestionar.py procesar_cobros` (para cron cada
   15 minutos): marca vencidas las cuentas con saldo, genera el cobro mensual
   (una sola vez por cliente y mes, desde el día configurado), programa los
   recordatorios (antes del vencimiento y cada N días en mora, sin repetir) y
   despacha los envíos cuya hora llegó. Idempotente.
7. Cada envío queda en el historial de **Comunicaciones** del cliente (canal,
   tipo manual/automático, usuario, éxito/fallo, reintentos).
8. `config/settings/local.py`: usa SMTP real si `CORREO_HOST` tiene valor;
   nueva variable `URL_SITIO` (base de los enlaces públicos; en producción
   debe ser el dominio real).
9. Documentación: ampliación de alcance en
   `md/Contanika_Especificaciones_Módulos.md` y `PLAN_TRABAJO.md` (T2 y T3
   resueltas); scripts SQL con las dos tablas nuevas y la fila inicial.

### Cómo verificarlo (entorno local)

```bash
cd /home/fredd/documentos/ubuntu/contanika/codigo
source .venv/bin/activate
python gestionar.py migrate
python gestionar.py runserver   # la fila de configuración del cobro se crea sola al abrirla
```

1. Detalle de una cuenta de cobro → "Enviar al cliente" → correo, ahora: el
   correo (con el PDF adjunto) aparece en la **consola de runserver**.
2. Mismo panel → WhatsApp: en el historial aparece «Abrir WhatsApp»; al
   pulsarlo se abre WhatsApp Web con el mensaje listo.
3. Honorarios → **Recordatorios de pago**: seleccionar, revisar la
   confirmación, enviar y ver el resumen.
4. Programar un envío para dentro de 2 minutos; esperar y en **Cobro
   automático** pulsar «Ejecutar ahora»: el envío se despacha.
5. **Cobro automático**: activar el cobro mensual con el día de hoy o uno
   anterior y pulsar «Ejecutar ahora»: se genera y envía la cuenta del mes de
   cada cliente con honorario; volver a ejecutarlo no duplica nada.

### Limitaciones conocidas

- Con `wa.me` no hay confirmación real de entrega: el WhatsApp se registra
  como enviado cuando el Administrador abre el enlace.
- El enlace al PDF solo funciona para el cliente cuando el sistema esté
  publicado en internet (`URL_SITIO` con el dominio real).
- La programación automática requiere el cron en el servidor; sin cron, los
  envíos programados salen al pulsar «Ejecutar ahora».

### Resultado de las pruebas

- Suite completa: **476 pruebas aprobadas**; finanzas suma 145 (72 nuevas de
  este bloque: `test_envios.py`, `test_procesar_cobros.py`,
  `test_vistas_envios.py`).
- Cobertura total **94 %**; finanzas: `envios.py` 100 %, selectores 100 %,
  servicios 99 %, formularios 98 %, vistas 96 %.
- Ruff (estilo y formato), bandit y pip-audit sin hallazgos.
- Seguridad: 403 para Contador Senior/Junior en todas las pantallas y acciones
  de envío; «Abrir WhatsApp» solo por POST (405 por GET); CSRF; redirección
  `siguiente` a sitios externos ignorada; token del PDF público alterado,
  vencido o de otra cuenta → 404; el envío masivo rechaza cuentas fuera del
  listado aunque se fuerce su id.

### Pendientes del Módulo 6

- **Bloque 3**: abonos con disparador PostgreSQL, panel de cartera e
  historial de abonos (HU016 parte 2, HU017, HU018).
- Configurar el correo real (`CORREO_*` en `.env`) cuando el despacho defina
  la cuenta.
- Programar el cron de `procesar_cobros` en WSL y en el hosting de producción.
- Reflejar en el documento Word la ampliación de alcance (HU/RQF nuevas) y las
  tablas `honorario_servicio`, `configuracion_cobro` y `envio_programado`.

---

## Viernes 25 de septiembre de 2026 — Módulo 6, bloque 3: abonos con disparador y panel de cartera

**Objetivo del bloque:** cerrar el Módulo 6 con el registro de pagos y abonos
con trazabilidad (HU016 parte 2), el panel de cartera (HU016-4, HU017) y el
historial de abonos en la ficha del cliente (HU018), e implementar el
**disparador (trigger)** que exige la guía del SENA.

Decisiones del usuario en esta sesión: el Contador Junior mantiene la gestión
de hallazgos de sus clientes (se aparta de la HU015); el cron de
`procesar_cobros` no se configura todavía; VS Code se reabrirá en WSL.

### Trabajo realizado

1. **Disparador de PostgreSQL** (migración `finanzas 0004`) sobre `abono`:
   - `trg_abono_calcular_saldo` (antes de insertar): bloquea la cuenta,
     calcula el **saldo anterior** y el **saldo resultante** y rechaza montos
     en cero o mayores que el saldo.
   - `trg_abono_actualizar_estado` (después de insertar): deja la cuenta en
     **Pagada**, **Vencida** (si ya venció y queda saldo) o **Abonada**.
   - `trg_abono_inmutable`: los abonos **no se modifican ni se eliminan**.
   La trazabilidad la garantiza la base de datos aunque se use otra vía
   distinta de la aplicación (pgAdmin, otro programa).
2. **Registrar pago** en el detalle de la cuenta (solo Administrador): fecha,
   monto, medio de pago del catálogo o uno nuevo escrito (se agrega al
   catálogo, como pide el spec), con validación previa del saldo. La tabla de
   pagos muestra saldo anterior, resultante y quién registró.
3. **Panel de cartera** (Honorarios → Cartera, todos los roles): por cliente,
   facturado, cobrado, saldo, cuentas pendientes y días de mora; rojo a más de
   30 días; ordenado por mora; totales arriba; opción de incluir clientes al
   día. Senior y Junior ven solo sus clientes (HU017-1).
4. **Ficha del cliente → Honorarios**: saldo pendiente destacado e historial de
   abonos del más reciente al más antiguo (HU018).
5. Admin de Django: los abonos quedan en solo lectura.
6. Script SQL: funciones y disparadores agregados en el formato de `pg_dump`.

### Cómo verificarlo (entorno local)

```bash
python gestionar.py migrate
python gestionar.py runserver
```

1. Detalle de una cuenta → **Pagos y abonos** → registrar un abono parcial:
   aparecen saldo anterior y resultante, y la cuenta pasa a "Abonada".
2. Registrar el resto: la cuenta pasa a "Pagada" y desaparece el formulario.
3. Intentar un monto mayor que el saldo: se rechaza.
4. **Honorarios → Cartera**: revisar totales, días de mora y el color rojo.
5. En pgAdmin: intentar `UPDATE abono SET monto = 1` o `DELETE FROM abono`
   → la base de datos lo rechaza (evidencia del disparador para el Word).

### Resultado de las pruebas

- Pruebas de finanzas: **170 aprobadas** (25 nuevas en `test_abonos.py`,
  ejecutadas contra el disparador real en PostgreSQL).
- `scripts/calidad.sh` completo en verde: **501 aprobadas**, cobertura 94 %.

### Pendientes del Módulo 6

- Evidencias para el Word: captura del panel de cartera, del historial de
  abonos y del rechazo del disparador en pgAdmin.
- Reflejar en el diccionario de datos las funciones y disparadores.

## Viernes 25 de septiembre de 2026 — Módulo 6: abonos visibles en tablas y PDF, envío masivo con fecha por cliente

**Pedido del usuario:** ver los abonos en las tablas de Honorarios, poder
seleccionar varios clientes con fechas distintas para enviar masivamente las
cuentas de cobro (programadas o todas de un solo clic) y que el PDF de la
cuenta muestre los abonos para que el cliente vea lo pendiente por pagar.

### Trabajo realizado

1. **Tablas con abonos:** el histórico de cuentas de cobro, la ficha del
   cliente (pestaña Honorarios) y el envío masivo muestran las columnas
   **Abonado** y **Saldo**. Al pulsar el valor abonado se despliega el detalle
   de los abonos de esa cuenta (fecha, medio, monto y saldo después del
   abono). Una sola consulta con agregación, sin una consulta por fila.
2. **PDF con abonos:** la cuenta de cobro trae la sección «Pagos y abonos
   recibidos» con cada abono, el valor de la cuenta, el total abonado y el
   **saldo pendiente por pagar** (resaltado); si ya está paga lo indica. El PDF
   se vuelve a generar cada vez que se registra un abono, así que el archivo
   que se descarga, se adjunta al correo y abre el cliente por WhatsApp está
   siempre al día.
3. **Envío masivo con fecha por cliente:** al elegir «Programar», la tabla
   muestra la columna **Fecha de envío** para cada cliente; la «fecha para
   todas» se puede copiar a las seleccionadas con un botón, y quien no tenga
   fecha propia usa la general. «Enviar ahora» sigue enviando todas de un
   solo clic (tras la confirmación que exige la HU046-3). La confirmación
   muestra la fecha de cada cliente. Se agregaron un **buscador de clientes**
   y la opción **incluir cuentas ya enviadas** para reenviarlas.
4. Corrección: el histórico fija su orden (más reciente primero), porque
   Django ignora el orden del modelo en consultas agregadas.

### Cómo verificarlo (entorno local)

1. Registrar un abono en una cuenta → en **Honorarios** aparecen Abonado y
   Saldo; pulsar el valor abonado para ver el detalle.
2. **Descargar PDF** de esa cuenta → sección de abonos y saldo pendiente.
3. **Envío masivo** → Cuándo: «Programar» → poner fechas distintas a dos
   clientes → Revisar el listado → Confirmar → **Envíos programados** muestra
   cada uno en su fecha.

### Resultado de las pruebas

- 14 pruebas nuevas (`test_abonos.py`, `test_vistas_envios.py`).
- `scripts/calidad.sh` completo en verde: **515 aprobadas**, cobertura 94 %,
  ruff, bandit y pip-audit sin hallazgos.

## Miércoles 30 de septiembre de 2026 — Módulo 6: disparadores aplicados en la BD local

1. Se aplicó `finanzas 0004_disparadores_abono` en `contanika_bd` (estaba
   pendiente: las pruebas lo usaban, pero la BD local no). Los tres
   disparadores quedan activos sobre `abono`.
2. **Corrección de datos:** los 3 abonos de prueba de la cuenta #2
   (registrados el 25-sep antes de existir el disparador) tenían saldo
   anterior y resultante en 0 y la cuenta seguía "Pendiente". Con aprobación
   del usuario, en una sola transacción se desactivó `trg_abono_inmutable`,
   se recalcularon los saldos en orden (1.100.000 → 600.000 → 250.000 →
   200.000), la cuenta quedó "Abonada" y se reactivó el disparador. Se
   regeneró el PDF de la cuenta.
3. Verificado: `UPDATE abono ...` vuelve a ser rechazado por el disparador;
   `check` y `ruff` sin hallazgos; pruebas de finanzas: **184 aprobadas**.

---

## Jueves 1 de octubre de 2026 — Módulo 9: expediente y bitácora por cliente

**Objetivo del bloque:** dejar navegable el Módulo 9 (HU025-HU027): registro
de anotaciones por cliente con archivos de soporte, consulta cronológica con
filtros y archivado por el Administrador. Rama `feature/modulo-9-expediente`
(creada desde `feature/modulo-6-finanzas`, ya subida a GitHub).

Decisiones del usuario en esta sesión:
- **Fecha del evento:** columna nueva `anotacion.fecha` (editable, por defecto
  hoy). `fecha_hora` sigue siendo el registro exacto automático (HU025-2).
- **Bitácora inmutable:** nadie edita ni elimina anotaciones, ni el autor.
- **Archivadas:** solo el Administrador archiva o restaura; se ocultan por
  defecto y cualquier rol puede verlas con el filtro «Incluir archivadas».

### Trabajo realizado

1. **Bitácora general** (menú → Expediente, y tarjeta del panel principal):
   anotaciones de todos los clientes visibles, en línea de tiempo, con filtros
   por cliente, tipo, rango de fechas e «Incluir archivadas»; paginada.
2. **Expediente del cliente** (`/expediente/cliente/<id>/`) con los mismos
   filtros, y pestaña **Expediente** en la ficha del cliente (últimas 10).
   El enlace «Ver expediente completo» del Kanban abre esa pestaña.
3. **Nueva anotación** (modal o página): cliente, tipo (los 9 del spec o uno
   escrito), fecha, contenido y archivos de soporte en un solo selector
   múltiple: hasta 5 (Administrador y Senior) o 3 (Junior), PDF/Word/Excel/
   imagen de máximo 10 MB. Queda registrada con el usuario y la hora exacta.
4. **Permisos:** los tres roles consultan, descargan adjuntos y anotan; el
   Junior solo en sus clientes asignados, pero ve las anotaciones de todo el
   equipo en ellos (HU027-5). Archivar/restaurar: solo el Administrador.
5. **Adjuntos:** se guardan en `media/adjuntos/anotaciones/<año>/<mes>/`
   (los de hallazgos siguen en `adjuntos/hallazgos/`). La validación de
   formato y tamaño se movió a `comunes` y la comparte Hallazgos.
6. Admin de Django: anotaciones en solo lectura (solo cambia «archivado»),
   sin agregar ni eliminar.
7. Script SQL: columna `fecha` e índice `idx_anotacion_cliente` actualizados.

### Cómo verificarlo (entorno local)

```bash
python gestionar.py migrate
python gestionar.py runserver
```

1. Ficha de un cliente → pestaña **Expediente** → **Nueva anotación**: tipo
   «Retención en la fuente», fecha de hace 6 meses, un PDF adjunto.
2. **Expediente completo y filtros** → filtrar por ese tipo y rango de fechas:
   aparece la anotación; descargar el PDF.
3. Como Administrador, **Archivar**: desaparece; marcar «Incluir archivadas»
   la muestra con la etiqueta «Archivada» y el botón **Restaurar**.
4. Como Contador Junior: solo aparecen sus clientes; no ve el botón Archivar
   y no puede adjuntar más de 3 archivos.

### Resultado de las pruebas

- 47 pruebas nuevas en `pruebas/expediente/` (cobertura del módulo 99-100 %).
- `scripts/calidad.sh` completo en verde: **562 aprobadas**, cobertura 94 %,
  ruff, bandit y pip-audit sin hallazgos.

### Pendientes del Módulo 9

- Aplicar las migraciones `comunes 0003` y `expediente 0002` en la BD local.
- Word: columna `fecha` en el diccionario de datos de `anotacion` y decisión
  de bitácora inmutable (HU026-4 decía «de otros usuarios»).
- Evidencias: capturas del expediente, filtros y archivado.

---

## Jueves 1 de octubre de 2026 — Módulo 7: comunicaciones integradas

**Objetivo del bloque:** dejar navegable el Módulo 7 (HU019-HU021, RQF008,
CU008): historial de comunicaciones por cliente con distinción visual entre
automáticas y manuales, filtros y registro manual de contactos hechos por
fuera de la plataforma. Rama `feature/modulo-7-comunicaciones` (creada desde
`feature/modulo-9-expediente`).

### Trabajo realizado

1. **Historial general** (menú → Comunicaciones): comunicaciones de todos los
   clientes visibles, de la más reciente a la más antigua, con filtros por
   cliente, canal, tipo y rango de fechas; paginado.
2. **Historial del cliente** (`/comunicaciones/cliente/<id>/`) y pestaña
   **Comunicaciones** en la ficha del cliente (últimas 10).
3. **Distinción visual:** etiqueta verde azulada «Automática» (con el módulo
   de origen, p. ej. Honorarios) y gris «Manual»; ícono por canal; los envíos
   fallidos se marcan en rojo.
4. **Registro manual** (Administrador y Senior; el Junior solo consulta):
   cliente, canal (llamada, reunión presencial o uno escrito, p. ej.
   videollamada), fecha y hora del contacto (por defecto ahora, no futura) y
   resumen obligatorio.
5. Nadie edita ni elimina comunicaciones; el admin de Django queda en solo
   lectura.
6. **Corrección del Módulo 6:** los envíos que el Administrador disparaba con
   un clic quedaban como «Manual». Según el spec, todo lo que envía el sistema
   es «Automática» y «Manual» es solo lo registrado a mano. Se corrigió el
   registro y la migración `comunicaciones 0002` actualiza los 2 registros
   existentes en la BD local.
7. Modelo: `canal` pasa a selección abierta y `fecha_hora` deja de fijarse
   sola para poder indicar cuándo fue la llamada (sin cambio de columnas).

### Cómo verificarlo (entorno local)

```bash
python gestionar.py migrate
python gestionar.py runserver
```

1. **Comunicaciones** en el menú: los 2 envíos del M6 aparecen como
   «Automática · Origen: Honorarios».
2. **Registrar comunicación** → Llamada, fecha de ayer, resumen → aparece como
   «Manual» en el historial y en la pestaña Comunicaciones del cliente.
3. Filtrar por canal «Llamada» y por tipo «Manual».

### Resultado de las pruebas

- 33 pruebas nuevas en `pruebas/comunicaciones/` y 1 en finanzas.
- `scripts/calidad.sh` completo en verde: **592 aprobadas**, cobertura 95 %,
  ruff, bandit y pip-audit sin hallazgos.

### Pendientes del Módulo 7

- Aplicar la migración `comunicaciones 0002` en la BD local.
- Cuando Calendario (alertas) o Documentos envíen por correo/WhatsApp, deben
  registrar su comunicación automática (hoy solo Honorarios envía).
- Word: canal como selección abierta y criterio automática/manual.

---

## Jueves 1 de octubre de 2026 — Módulo 8: gestión de equipo y roles

**Objetivo del bloque:** dejar navegable el Módulo 8 (HU022-HU024, HU050,
RQF009, RQF029, RQF031): usuarios del equipo, módulos por rol, panel de
trabajo del equipo y perfil propio. Rama `feature/modulo-8-equipo` (creada
desde `feature/modulo-7-comunicaciones`).

Decisiones del usuario en esta sesión:
- **Correo de bienvenida** con el usuario (correo) y la contraseña temporal.
- **Eliminar** solo usuarios sin historial; con historial se inactivan.

### Trabajo realizado

1. **Usuarios** (Equipo y roles → Usuarios, solo Administrador): listado con
   filtros por nombre/correo, rol y estado; crear (nombre, correo, teléfono,
   rol y contraseña temporal) mostrando los módulos del rol elegido antes de
   confirmar; editar datos, correo, rol y asignar una nueva clave temporal;
   activar/inactivar; eliminar solo si no tiene registros asociados.
2. **Reglas de administradores:** siempre queda al menos un Administrador
   activo; tener más de uno exige confirmarlo; nadie se inactiva ni se
   elimina a sí mismo.
3. **Módulos por rol** (HU050): tabla de interruptores módulo × rol. Un módulo
   inhabilitado desaparece del menú y su URL muestra «Acceso no disponible»
   (nueva página 403); los datos se conservan. El Administrador no puede
   quitarse el módulo de equipo.
4. **Panel de equipo** (Administrador y Senior, solo consulta): por miembro,
   tareas activas, % completado de las tareas que vencen en el mes,
   vencimientos de los próximos 7 días y alerta «Sobrecarga» con más de 10
   pendientes; se recarga cada minuto.
5. **Mi perfil** (clic en el nombre o el avatar; todos los roles): nombre,
   teléfono y foto; firma, identificación y tarjeta profesional para
   Administrador y Senior; cambio de contraseña exigiendo la actual. El correo
   y el rol solo los cambia el Administrador. La foto aparece en la barra.
6. `usuario.foto_url` (URL sin carga) pasa a `foto` (imagen), migración
   `seguridad 0004`.
7. **Corrección:** las tarjetas del panel principal de Comunicaciones y
   Expediente salían como «Próximamente»; ahora las rutas se toman del menú.
8. Menú: «Equipo y roles» se oculta al Contador Junior (no tiene funciones
   ahí; su perfil está siempre disponible).

### Cómo verificarlo (entorno local)

```bash
python gestionar.py migrate
python gestionar.py runserver
```

1. **Equipo y roles → Usuarios → Nuevo usuario**: crear un Contador Junior
   con una contraseña temporal (mínimo 10 caracteres). El correo de
   bienvenida aparece en la consola de `runserver`.
2. Cerrar sesión y entrar como ese Junior: no ve «Equipo y roles»; en **Mi
   perfil** cambia su contraseña.
3. Como Administrador, **Módulos por rol** → apagar Clientes para el Junior →
   el Junior deja de verlo y la URL muestra «Acceso no disponible».
4. **Panel de equipo**: tareas y vencimientos por miembro.

### Resultado de las pruebas

- 59 pruebas nuevas en `pruebas/seguridad/`.
- `scripts/calidad.sh` completo en verde: **645 aprobadas**, cobertura 95 %,
  ruff, bandit y pip-audit sin hallazgos.

### Pendientes del Módulo 8

- Aplicar la migración `seguridad 0004` en la BD local.
- Word: `usuario.foto` en el diccionario de datos y las reglas de
  administradores y de eliminación.

---

## Jueves 1 de octubre de 2026 — Módulo 10: reportes y análisis, y sección de ayuda

**Objetivo del bloque:** construir el último módulo funcional (HU028, HU029,
HU048, HU051, RQF015, RQF026) con los seis reportes exportables en Excel y
PDF, y la sección de ayuda (HU053). Rama `feature/modulo-10-reportes` (creada
desde `feature/modulo-8-equipo`, ya subida a GitHub).

Decisiones del usuario en esta sesión:
- **Registro de descargas:** tabla nueva `descarga_reporte` (40 tablas).
- **Ayuda (HU053)** incluida en este bloque.

### Trabajo realizado

1. **Seis reportes** (menú → Reportes), cada uno con filtros, vista previa en
   pantalla y descarga en **Excel** o **PDF**:
   - *Clientes*: datos fiscales, municipios, servicios, contacto, responsable,
     estado; filtros por régimen, ciudad, estado, servicio, responsable y
     fecha de registro.
   - *Vencimientos tributarios* (HU029): filtros por período, cliente, tipo,
     ámbito, estado y responsable; vencidos sin presentar en rojo.
   - *Cartera*: honorario configurado, facturado, cobrado, deuda acumulada,
     días e indicador de mora (crítica en rojo) e historial de abonos;
     **gráfico** de deuda por cliente (10 mayores).
   - *Cuentas de cobro*: período, descripción del servicio, valor, abonado,
     saldo, estados de envío y pago, vencimiento; vencidas en rojo.
   - *Tareas del Kanban* (HU051): cliente, tipo, responsable, prioridad,
     vencimiento, estado e historial de cambios; vencidas en rojo.
   - *Ingresos mensuales* (HU048): facturado, cobrado, pendiente y en mora por
     mes con **gráfico de barras**, comparativo con el mes anterior, promedio
     mensual y los tres clientes con mayor saldo. Solo consolidado.
2. **Excel:** cifras como números con formato de pesos y fechas, filas en rojo
   y una hoja «Gráfico» con el gráfico de barras nativo de Excel. **PDF:**
   horizontal, con membrete del despacho, filtros usados, resumen, gráfico y
   tablas.
3. **Datos por rol:** Senior y Junior solo ven sus clientes asignados; el de
   ingresos es el total del despacho.
4. **Visibilidad por rol** (Administrador): interruptores reporte × rol; un
   reporte oculto no aparece en la vista del rol ni abre por URL.
5. **Historial de descargas** (Administrador): quién descargó qué reporte,
   cuándo, en qué formato y con qué filtros (HU028-5).
6. **Ayuda** (ícono «?» en la barra superior, todos los roles): guía corta de
   los 10 módulos, preguntas frecuentes y contacto del despacho.
7. Script SQL: tabla `descarga_reporte` (40 tablas). Con los dos gráficos y el
   disparador del M6 queda cubierto lo que pide la guía del SENA (3 reportes
   planos, 2 gráficos, 1 disparador).

### Cómo verificarlo (entorno local)

```bash
python gestionar.py migrate
python gestionar.py runserver
```

1. **Reportes → Ingresos mensuales**: gráfico, comparativo y top 3; descargar
   Excel (abrir la hoja «Gráfico») y PDF.
2. **Reportes → Vencimientos tributarios**: filtrar por ámbito y descargar;
   los vencidos sin presentar salen en rojo.
3. **Historial de descargas**: aparecen las dos descargas con sus filtros.
4. **Visibilidad por rol**: ocultar Ingresos al Contador Junior.
5. Ícono **?** de la barra superior → Ayuda.

### Resultado de las pruebas

- 45 pruebas nuevas en `pruebas/reportes/` (cobertura del módulo 96 %).
- `scripts/calidad.sh` completo en verde: **688 aprobadas** (antes de las 2
  últimas), cobertura 95 %, ruff, bandit y pip-audit sin hallazgos.

### Pendientes del Módulo 10

- Aplicar la migración `reportes 0002` en la BD local.
- Word: tabla `descarga_reporte` en el diccionario de datos; el reporte de
  credenciales sigue en el M1 sin descarga (la HU028 lo lista en el M10).
- Evidencias: capturas de cada reporte, el Excel con su gráfico y el PDF.

## Jueves 1 de octubre de 2026 — Verificación del script SQL (entregable 3.1)

Se cargaron `01_esquema_contanika.sql` y `02_datos_iniciales.sql` con `psql`
(`ON_ERROR_STOP`) en una base temporal aparte, que luego se eliminó.

1. **El esquema no cargaba:** los `COMMENT ON TABLE` estaban al inicio, antes
   de crear las tablas, y sin esquema (el volcado de `pg_dump` deja vacío el
   `search_path`). Se movieron al final del script como `public.<tabla>`.
2. **Faltaba una columna:** `vencimiento.periodo_gravable` (agregada en el
   Módulo 2) no estaba en el script.
3. Resultado: ambos scripts cargan sin errores; 40 tablas, todas con su
   comentario, y los 3 disparadores de `abono`. La comparación columna por
   columna (tipo, longitud y nulabilidad) con la BD local da 252 columnas
   idénticas, sin diferencias.

Nota: el script trae los comandos `\restrict`/`\unrestrict` de `pg_dump` 16,
propios de `psql`; para cargarlo usar `psql -f`, no la herramienta de
consultas de pgAdmin.

## Jueves 1 de octubre de 2026 — Cálculo de vencimientos al registrar un cliente

**Problema reportado:** al registrar un cliente con su NIT o cédula no se
calculaban los vencimientos (p. ej. la renta de una persona natural, que
depende de los dos últimos dígitos del documento).

**Causas encontradas** (revisando los clientes de la BD local):
1. El cálculo solo corría al pulsar «Calcular vencimientos» en la ficha; al
   guardar el cliente no pasaba nada.
2. El grupo DIAN se decidía por el tipo de documento: NIT → 1 dígito, cédula →
   2 dígitos. Una persona natural registrada con NIT buscaba «5» y la renta de
   personas naturales está cargada como «05»; con cédula pasaba al revés con
   IVA y retención (que van por el último dígito). No encontraba fechas.
3. Clientes sin obligaciones marcadas quedaban con el calendario vacío sin
   ninguna explicación.

**Cambios:**
- `calendario.servicios.calcular_grupo_nit` → `calcular_grupos_dian`: devuelve
  el último dígito y los dos últimos, y la búsqueda toma el grupo que exista
  para cada obligación. Funciona igual con NIT o cédula.
- Al crear o editar un cliente se calculan sus vencimientos (si el rol tiene
  el M2 habilitado) y se muestra el resultado. Si no marcó obligaciones, un
  aviso le pide elegir qué impuestos o anticipos presenta.
- Nuevo aviso `sin_coincidencia`: obligaciones con fechas cargadas pero
  ninguna para ese documento (p. ej. «Renta personas jurídicas» en una
  persona natural). También aparece en «Calcular vencimientos» de la ficha.

- **Fechas corregidas no se pisan:** como ahora se recalcula en cada guardado,
  recalcular ya no cambia un vencimiento «Validado». Al editar la fecha de un
  vencimiento automático DIAN, queda «Validado»
  (`servicios.guardar_vencimiento_editado`; el spec dice que el contador lo
  valida tal cual o lo modifica).

**Verificación:** 163 pruebas de `calendario` y `clientes` en verde (8 nuevas),
`ruff` sin hallazgos. En la BD local se calculó para los clientes 15, 16 y 18
(en el 18, de `1019087764`, se marcó «Renta personas naturales» y salió el
25-sep-2026, grupo 64).

### Pendientes
- Cliente 17 (NIT `5555555555`): tiene una renta manual (28-sep, sin período)
  y la tabla DIAN trae 21-sep (grupo 55); no se recalculó para no duplicarla.
  Decidir con el usuario cuál conservar.
- `sin_coincidencia` solo avisa si no hay fecha para el documento; una renta
  de personas jurídicas marcada a una persona natural genera fecha si el último
  dígito coincide. Evaluar un aviso por tipo de persona.
- Evaluar si conviene sugerir obligaciones por tipo de persona al crear.

## Jueves 1 de octubre de 2026 — Sincronía de información para el Contador Junior

**Pedido del usuario:** como Contador Junior debe poder gestionar clientes, ver
las tareas que le asignan otros roles y las anotaciones del calendario, o sea
trabajar con la misma información que el equipo. Decisiones (preguntadas):
clientes crear/editar y ver todos; tareas las suyas y las de sus clientes;
calendario completo del despacho.

**Cambios:**
- **Clientes (M1):** el Junior ve todos los clientes, crea y edita cualquiera
  (`ROLES_GESTIONAN`). El formulario no le ofrece «Responsable» ni «Estado»: el
  cliente nuevo queda a su nombre y el existente conserva responsable y estado.
  Sigue sin inactivar ni importar. Las credenciales solo se muestran en los
  clientes a su cargo (la pestaña no aparece en los demás), siempre sin editar.
- **Tareas (M3):** `tareas_visibles` incluye, además de las asignadas a él, las
  de los clientes que tiene a su cargo. Solo cambia el estado y agrega
  observaciones a las suyas (`puede_actualizar_tarea`; en la tarjeta ajena se
  ocultan el selector de estado y el formulario de observaciones, y no se
  puede arrastrar).
- **Calendario (M2):** `vencimientos_visibles` ya no filtra por rol: el Junior
  ve todos los vencimientos y consulta su detalle (sin editar). Las anotaciones
  ya se mostraban según su visibilidad (Equipo, su rol o etiquetadas); se
  agregó una prueba de que ve las del equipo y no las privadas.
- Hallazgos, documentos, expediente, comunicaciones, finanzas y reportes siguen
  limitados a los clientes asignados: en la ficha de un cliente ajeno esas
  pestañas aparecen vacías para el Junior.

**Verificación:** 225 pruebas de `clientes`, `calendario` y `tareas` en verde;
se reescribieron 8 pruebas que verificaban la regla anterior y se agregaron 12 nuevas.

### Pendientes
- Word: HU del Junior en clientes («puede ver pero no editar el perfil»,
  «solo ve los clientes asignados»), calendario («solo los vencimientos de sus
  clientes») y tareas («solo las asignadas a su usuario»); credenciales solo en
  clientes a cargo.
- Decidir si hallazgos, documentos, expediente y comunicaciones también se
  abren al Junior para todos los clientes (hoy vacíos en clientes ajenos).
- El Junior no puede marcar vencimientos como «En progreso/Presentada» aunque
  la HU de calendario lo dice (criterio 4); hoy solo Administrador y Senior.

## Jueves 1 de octubre de 2026 — Cierre de huecos de los módulos 1, 2 y 5-9

**Pedido:** hacer las correcciones necesarias tras la revisión de los módulos.

1. **Junior: lectura en toda la ficha del cliente.** Hallazgos, documentos,
   expediente y comunicaciones ahora se consultan para todos los clientes
   (`hallazgos_visibles`, `documentos_visibles`, `expediente.clientes_visibles`
   y `anotaciones_visibles`, `comunicaciones`). La escritura sigue limitada a los
   clientes asignados con selectores aparte (`hallazgos_gestionables`,
   `clientes_para_generar`, `clientes_anotables`); en un hallazgo ajeno el detalle
   es de solo lectura y en la ficha de un cliente ajeno se ocultan los botones
   de crear (`a_cargo`). Finanzas y reportes no cambian.
2. **Junior marca el avance de vencimientos** (HU de calendario, criterio 4):
   `puede_actualizar_estado` (clientes a su cargo o vencimientos de los que es
   responsable). Validar y editar siguen siendo del Administrador y el Senior.
3. **Reporte de credenciales consolidado** (M1, spec): `clientes/credenciales/reporte/`,
   con filtros por cliente y estado, sin descarga; el Junior solo ve las de sus clientes.
4. **Alertas automáticas del Calendario** (HU040, el mayor hueco: se configuraban
   pero nada las disparaba):
   - Columna `configuracion_alerta.fecha_envio` (migración `calendario 0004`,
     aplicada en la BD local).
   - `servicios.procesar_alertas` y comando `procesar_alertas` (cron): envía por
     correo al responsable, registra la `Comunicacion` automática, no repite, reintenta
     si falla y vuelve a avisar si el vencimiento cambia de fecha.
   - Campana en la barra superior con los vencimientos próximos del usuario
     (siempre visible, aunque falle el correo) y enlace `wa.me` para las alertas
     de WhatsApp. WhatsApp no se marca como enviada: una persona pulsa Enviar (T2).
5. **Script SQL (entregable 3.1):** faltaban las tablas `obligacion_tributaria` y
   `cliente_obligacion` (agregadas en el M1, nunca llegaron al script) y el
   catálogo de 10 obligaciones. Se agregaron junto con `fecha_envio`. Verificado
   cargando ambos scripts con `psql` (`ON_ERROR_STOP`) en una base temporal:
   **42 tablas**, 42 comentarios, 259 columnas idénticas a la BD local, 3
   disparadores de `abono`, 10 obligaciones sembradas.
6. Prueba de reportes que fallaba de noche (fecha UTC vs. Bogotá) corregida.

**Verificación:** 744 pruebas en verde; `ruff`, `bandit` y `check` sin hallazgos.

### Pendientes
- Cron en WSL y producción: `procesar_alertas` (cada hora) y `procesar_cobros`.
- Word: tabla `configuracion_alerta` (columna `fecha_envio`), tablas
  `obligacion_tributaria` y `cliente_obligacion` (son 42 en total, no 36),
  HU del Junior (clientes, tareas, calendario, hallazgos, documentos, expediente,
  comunicaciones y credenciales) y HU040 (la alerta de WhatsApp es un enlace).
- Cliente 17: decidir cuál renta conservar (manual 28-sep o tabla DIAN 21-sep).

## Jueves 1 de octubre de 2026 — PDF: firma a la izquierda y ciudad centrada

**Pedido del usuario:** en los PDF con firma, la firma debe ir al costado
izquierdo y la ciudad debe ser congruente con su posición y el texto.

Se revisaron los PDF reales (certificado y cuenta de cobro):
- La firma salía centrada (ReportLab centra las imágenes) mientras el nombre,
  la cédula y la tarjeta profesional estaban a la izquierda; además se
  estiraba a 5 × 2,5 cm fijos y se deformaba.
- «Bogotá D.C.» quedaba suelta a la izquierda bajo el nombre del despacho,
  que va centrado.

**Cambios:**
- `comunes/pdf.py`: `imagen_proporcional(ruta, ancho, alto, alineacion)` escala
  sin deformar; `encabezado_despacho` centra la ciudad bajo el nombre (aplica a
  documentos, cuentas de cobro y reportes).
- `documentos/servicios.bloque_firma`: firma alineada a la izquierda y a
  escala, con los datos del contador debajo, en un `KeepTogether` para que un
  salto de página no los separe. Los datos del contador ahora se escapan.

**Verificación:** vista previa con el documento 2 y la cuenta 3 de la BD local
(sin guardar); 297 pruebas de documentos, finanzas y reportes en verde (4 nuevas).
Los PDF ya generados conservan el diseño anterior; los nuevos salen con este.

### Pendientes
- Los meses salen con mayúscula («1 de Octubre de 2026»); en español van en
  minúscula. Preguntar al usuario si se corrige en todos los PDF y mensajes.

## Jueves 1 de octubre de 2026 — Barrido de colores: fuera el azul de Bootstrap

**Pedido del usuario:** revisar todos los módulos y verificar que los colores
concuerden con la paleta de la plataforma; notaba un azul que no armoniza.

**Diagnóstico** (49 páginas de los 10 módulos renderizadas con la BD local, solo
lectura, y capturadas con el navegador sin ventana): el azul era el color
primario de Bootstrap (`#0d6efd`), que aparecía en todo componente que
`contanika.css` no reemplazaba: pestañas (ficha del cliente, Equipo y roles),
enlaces sin clase, casillas e interruptores (módulos por rol, visibilidad de
reportes, envío masivo), avisos informativos, acordeón de Ayuda, desplegables,
barras de progreso y anillos de foco. Los botones solo estaban corregidos en
su estado normal: pulsados o deshabilitados volvían al azul.

**Cambios:**
- `contanika.css`, sección «Armonía con Bootstrap»: se reemplazan las
  variables de color de Bootstrap (`--bs-primary`, `--bs-link-color`,
  `--bs-info`, `--bs-focus-ring-color` y sus variantes) por el teal y el navy de
  la paleta, más las reglas de casillas, interruptores, acordeón, desplegables y
  controles nativos (`accent-color`, selección de texto). Los botones se definen
  con las variables `--bs-btn-*` para cubrir todos los estados.
- Calendario: los vencimientos municipales usaban un morado ajeno a la paleta;
  ahora usan el marrón (`--brown`).
- `comunes/paleta.py`: la paleta para lo que se genera fuera del navegador. La
  usan los reportes (encabezados de tabla, series de los gráficos en pantalla,
  PDF y Excel) y la cuenta de cobro (encabezado, rejilla y fila de saldo). El
  gráfico de Excel no fijaba colores y salía con el azul del tema de Office.

**Verificación:** el azul de Bootstrap pasó de 133.189 píxeles a 0 en las 49
páginas (medido sobre las capturas de antes y después). 765 pruebas en verde;
las nuevas amarran la paleta de PDF/Excel a las variables del CSS y fallan si
vuelve a aparecer el azul de Bootstrap en la hoja de estilos.

### Pendientes
- Los estados que solo aparecen al interactuar (foco, pulsado, acordeón
  abierto) se corrigieron por las variables pero no quedaron en captura:
  revisarlos en pantalla.
- Los PDF ya generados conservan los colores anteriores.

## Viernes 2 de octubre de 2026 — Panel principal como tablero gráfico

**Pedido del usuario:** mejorar el panel principal: quitar los módulos y armar
secciones útiles (vencimientos, finanzas, tareas y otros temas) con interfaz
gráfica.

**Cambios:**
- Se quitó la cuadrícula «Módulos del sistema» (repetía el menú lateral) y las
  cuatro cifras anteriores (clientes activos/inactivos, servicios, usuarios).
- Franja de cifras con enlace al módulo: vencen en 7 días, vencidos sin
  presentar, tareas atrasadas, cartera por cobrar (con lo que está en mora),
  hallazgos abiertos y clientes activos. El color del ícono avisa (rojo si hay
  vencidos, atrasadas o mora).
- **Vencimientos:** por presentar esta semana y la próxima, presentados del
  mes, gráfico de barras por semana de las próximas 8 semanas (por presentar y
  presentados) y lista de lo más urgente (hasta 2 vencidos y los que siguen).
- Distribución en dos columnas parejas (pedido del usuario): Vencimientos y
  Finanzas en la primera fila, con la misma estructura (cifras, gráfico,
  lista); Tareas y Hallazgos en la segunda; Carga del equipo al final.
- **Tareas:** barras por columna del Kanban, avance del tablero y las próximas
  tareas del usuario (si no tiene, las del equipo que puede ver).
- **Finanzas:** facturado y cobrado del mes, saldo en mora, gráfico de los
  últimos 6 meses, recaudo acumulado y clientes con saldo pendiente.
- **Hallazgos** sin cerrar por estado y prioridad, y **carga del equipo**
  (Administrador y Senior).
- `aplicaciones/seguridad/panel.py` (nuevo) arma las secciones con los
  selectores de visibilidad de cada módulo: el Junior ve en Finanzas solo sus
  clientes y en Tareas solo las que ya veía. Un módulo inhabilitado para el rol
  no aparece. Sin migraciones ni cambios en la base de datos.
- Colores de los gráficos tomados de `comunes/paleta.py` y comprobados para
  daltonismo; cada gráfico tiene su tabla de datos desplegable.
- Responsive (requisito recordado por el usuario): revisado en 360, 390, 768,
  1024, 1280 y 1440 px. En teléfono las cifras de cada sección pasan a filas
  «etiqueta – valor», los clientes con saldo muestran el nombre completo con el
  monto debajo y los gráficos omiten etiquetas en vez de girarlas.

### Cómo verificarlo (entorno local)
Entrar a `http://127.0.0.1:8000/` con Paula (Administrador) y con un Contador
Junior: el Junior no ve «Carga del equipo» y sus cifras de Finanzas son solo de
sus clientes. Las tarjetas y las filas de las listas llevan al detalle.

### Resultado de las pruebas
`pruebas/seguridad/test_panel.py` (17 pruebas nuevas): cifras de cada sección,
agrupación por semana, visibilidad por rol, módulo inhabilitado y la vista. Se
retiró la prueba de las tarjetas de módulos.

### Pendientes
- En la BD local hay muchos vencimientos de 2026 ya pasados que siguen en
  «Pendiente»; el panel los cuenta como vencidos sin presentar. Decidir con el
  usuario si se marcan como presentados o si el conteo debe partir de una fecha.
- Captura del panel para el Word.
- **pr01 — endurecimiento de seguridad** (pedido del usuario, 1-oct-2026; se
  ejecuta solo cuando él avise). Antes de implementar, auditar qué cubre ya
  Django y el proyecto y qué falta. Los 20 controles:
  1. Ocultar las claves API.
  2. Eliminar secretos de Git.
  3. Usar una clave pública de BD.
  4. Activar RLS.
  5. Cifrar datos sensibles.
  6. Forzar autenticación del servidor.
  7. Restringir acceso a registros.
  8. Bloquear manipulación de campos.
  9. Proteger cookies de sesión.
  10. Hashear contraseñas.
  11. Limitar intentos de inicio de sesión.
  12. Añadir protección contra bots.
  13. Monitorizar consultas de BD.
  14. Validar todas las entradas.
  15. Escapar contenido del usuario.
  16. Restringir subida de archivos.
  17. Limitar respuestas de API.
  18. Añadir cabeceras de seguridad.
  19. Forzar HTTPS.
  20. Escanear dependencias.


---

## Martes 6 de octubre de 2026 — Guías paso a paso en la ayuda, mapa de navegación y cron

### Qué se hizo
- **Ayuda con guías de procesos** (pedido del usuario; amplía la HU053): 21
  guías paso a paso (crear un cliente, importar desde Excel, calcular
  vencimientos, generar una cuenta de cobro, registrar un abono, crear un
  usuario, etc.) en `aplicaciones/seguridad/guias.py`. Cada guía trae resumen,
  «Antes de empezar», pasos numerados con los nombres reales de botones y
  campos, notas, guías relacionadas y un botón que lleva a la pantalla.
  - Cada usuario ve solo las guías de lo que puede hacer: se filtran por rol y
    por módulo habilitado. Una guía ajena responde 403 y una inexistente 404.
  - `seguridad:ayuda` lista las guías por módulo con un buscador (sin tildes ni
    mayúsculas); `seguridad:guia` (`/ayuda/guias/<slug>/`) muestra una.
  - Se corrigió una pregunta frecuente que decía que el Junior solo veía sus
    clientes (ya no es así desde el 1-oct).
- **Buscador de la barra superior:** estaba deshabilitado («Disponible al
  completar el módulo de clientes»). Ahora busca por nombre o razón social y
  lleva al listado de clientes; no aparece si el rol no tiene el Módulo 1.
- **Mapa de navegación (entregable 3.3):** comando
  `python gestionar.py generar_mapa_navegacion`, que lee las rutas reales y
  escribe `documentacion/MAPA_NAVEGACION.md`: diagrama general, diagrama y
  tabla por módulo (ruta, métodos, acceso por rol, qué hace) y resumen de
  acceso por rol y módulo. 107 rutas.
- **Cron:** `scripts/instalar_cron.sh` programa `procesar_cobros` (cada 15
  minutos) y `procesar_alertas` (cada hora), con registros en `registros/`.
  Tiene `--ver` y `--quitar`. **No se instaló**: en la BD local el cobro
  automático está activo y el cron generaría cuentas de cobro reales; lo
  ejecuta el usuario cuando lo decida.
- **Lista de cambios para el Word:** `documentacion/CAMBIOS_WORD.md` (stack,
  6 tablas nuevas con sus columnas, columnas cambiadas, disparadores, alcance,
  historias de usuario modificadas, entregables y capturas pendientes).

### Cómo verificarlo (entorno local)
Pulsar el ícono de ayuda de la barra superior: aparecen las guías agrupadas por
módulo. Abrir «Crear un cliente» y seguir el botón «Ir a Nuevo cliente». Entrar
como Contador Junior: no ve las guías de honorarios ni de usuarios. Escribir un
nombre en el buscador de la barra superior y pulsar Enter.

### Resultado de las pruebas
`pruebas/seguridad/test_ayuda.py` (catálogo, visibilidad por rol y módulo,
vistas, escape de texto y buscador) y `pruebas/seguridad/test_mapa_navegacion.py`.
Responsive revisado en 360, 768, 1024 y 1440 px.

### Pendientes
- Instalar el cron (`bash scripts/instalar_cron.sh`) cuando el usuario lo decida.
- Capturas de la ayuda para el Word.
- Si cambia un botón, un campo o un permiso, actualizar su guía en `guias.py`.
- Siguen abiertos los pendientes del 2 de octubre (vencimientos pasados en
  «Pendiente», captura del panel y **pr01**).


---

## Miércoles 7 de octubre de 2026 — Contador Junior sin panel ni honorarios, y Ayuda en el menú

### Qué se hizo
Pedido del usuario tras entrar con el perfil del Contador Junior.
- **Panel principal:** el Junior ya no lo ve. No aparece en su menú y, al
  entrar o abrir `/`, llega a su primer módulo: Calendario; si no lo tiene,
  Tareas; si no, la primera entrada de su menú (`menu.ruta_de_inicio`).
  Administrador y Senior siguen igual.
- **Honorarios y reportes financieros del Junior:** quedan inhabilitados de
  entrada el Módulo 6 y los reportes de Cartera, Cuentas de cobro e Ingresos
  mensuales del despacho. Es el valor inicial (`cargar_datos_iniciales` y
  `scripts/bd/02_datos_iniciales.sql`); el Administrador lo cambia cuando
  quiera en Equipo y roles → «Módulos por rol» y Reportes → «Visibilidad por
  rol», y el comando no pisa lo que él configure.
  - En la BD local se actualizaron esas cuatro filas del rol Contador Junior
    (`permiso_rol_modulo` y `permiso_reporte_rol`).
- **Ficha del cliente:** la pestaña «Honorarios» ya no aparece (ni se
  consultan sus datos) si el rol no tiene el Módulo 6. Antes se mostraba
  aunque el módulo estuviera inhabilitado.
- **Ayuda en el menú lateral:** nueva sección «Soporte» con la opción «Ayuda»,
  visible para todos los roles; se conserva el ícono de la barra superior.

### Cómo verificarlo (entorno local)
Entrar como Contador Junior: llega al Calendario; el menú no tiene «Panel» ni
«Honorarios» y sí «Ayuda»; en Reportes solo ve Clientes, Vencimientos y Tareas;
la ficha de un cliente no tiene la pestaña «Honorarios»; `/honorarios/`
responde 403. Entrar como Paula: todo igual, con «Ayuda» en el menú.

### Resultado de las pruebas
`pruebas/seguridad/test_panel.py`: inicio del Junior, Ayuda en el menú, ficha
sin honorarios y valores iniciales de permisos (sin pisar cambios).

### Pendientes
- Las demás pestañas de la ficha del cliente (vencimientos, documentos,
  hallazgos, expediente, comunicaciones) se siguen mostrando aunque su módulo
  esté inhabilitado para el rol; el módulo sí bloquea sus pantallas. Decidir si
  se ocultan igual que «Honorarios».
- Siguen abiertos: instalar el cron, capturas, vencimientos pasados en
  «Pendiente» y **pr01**.


---

## Miércoles 7 de octubre de 2026 — Visibilidad por rol configurable y ayuda en tres columnas

### Qué se hizo
Aclaración del usuario: lo que ven los roles no administradores lo debe poder
activar o desactivar él, no quedar fijo en el código. Rama
`feature/visibilidad-por-rol`, creada desde `main`.
- **Panel principal configurable:** en el bloque anterior quedó oculto para el
  Junior de forma fija; ahora es una fila más de Equipo y roles → «Módulos por
  rol» («Panel principal», código `PANEL` en el catálogo `modulo`). Vale para
  cualquier rol. Migración `seguridad 0005` (cambia las opciones del campo y,
  en instalaciones con datos, crea la fila y sus permisos: habilitado para
  todos menos para el Junior).
- **Pestañas de la ficha del cliente:** Vencimientos, Documentos, Hallazgos,
  Honorarios, Expediente y Comunicaciones aparecen solo si el rol tiene
  habilitado el módulo correspondiente; si no, tampoco se consultan sus datos.
- **Matriz de módulos:** texto que explica qué oculta cada interruptor y botón
  «Reportes por rol» hacia la visibilidad de reportes.
- **Ayuda en tres columnas** (pedido del usuario): las guías ocupan todo el
  ancho y los módulos se reparten en tres columnas (dos en tableta, una en
  teléfono), cada módulo con sus guías apiladas; debajo, tres columnas parejas
  con la guía rápida, las preguntas frecuentes y el soporte.
- Datos iniciales (`cargar_datos_iniciales` y `02_datos_iniciales.sql`) con la
  fila del panel. Se aplicó la migración en la BD local.
- **Tareas visibles para todo el equipo** (regla del usuario: clientes,
  vencimientos y tareas se ven completos para que la información esté
  sincronizada). Clientes y vencimientos ya lo estaban desde el 1-oct; faltaban
  las tareas, que el Junior solo veía si eran suyas o de sus clientes. Ahora ve
  el tablero completo y el filtro le ofrece todos los clientes; sigue pudiendo
  mover y comentar solo las tareas asignadas a él.
- **Reportes de clientes, vencimientos y tareas** con la información de todo el
  despacho para Senior y Junior (antes, solo sus clientes asignados), para que
  coincidan con lo que ven en los módulos. Modifica HU029-1 y HU051-4. Cartera
  y cuentas de cobro siguen limitados a los clientes asignados.

### Cómo verificarlo (entorno local)
Como Paula, en Equipo y roles → «Módulos por rol», activar «Panel principal»
para el Contador Junior y guardar: el Junior vuelve a ver el panel. Desactivar
«Hallazgos» para un rol: desaparece del menú, de la ficha del cliente y del
panel de ese rol.

### Resultado de las pruebas
`pruebas/seguridad/test_panel.py`: panel por rol desde la matriz, pantalla de
inicio sin panel y una prueba por cada pestaña de la ficha. Ayuda y matriz
revisadas en 360, 768, 1024 y 1440 px.

### Pendientes
- Los mismos del bloque anterior (cron, capturas, vencimientos pasados, **pr01**).


---

## Miércoles 7 de octubre de 2026 — Fase 4: pase de calidad, matriz CRUD y seguridad transversal

### Qué se hizo
Rama `feature/fase-4-calidad`, creada desde `main`.
- **Pase de calidad completo:** `ruff`, `bandit` y `pip-audit` sin hallazgos;
  cobertura del 96 % (el archivo más bajo, 77 %). `check --deploy` con la
  configuración de producción deja un solo aviso: la `SECRET_KEY` es la de
  desarrollo.
- **Matriz CRUD y de seguridad:** `documentacion/MATRIZ_CRUD_SEGURIDAD.md`.
  Por módulo, quién crea, consulta, actualiza y elimina cada entidad; por
  riesgo, su control y dónde se prueba; y el resultado del pase de calidad.
- **Pruebas de seguridad sobre todas las rutas**
  (`pruebas/seguridad/test_seguridad_transversal.py`): toman las rutas del
  recorrido del mapa de navegación y comprueban, en cada una, acceso sin
  sesión, POST sin token CSRF, rol no permitido y módulo inhabilitado. Además,
  el bloqueo por fuerza bruta de django-axes, que no tenía prueba, y que las
  únicas rutas públicas sean el inicio de sesión y el PDF firmado. Una ruta
  nueva queda cubierta sin escribir su prueba.

### Cómo verificarlo
`bash scripts/calidad.sh` y
`pytest pruebas/seguridad/test_seguridad_transversal.py`.

### Pendientes
- Generar una `SECRET_KEY` real en el `.env` del servidor al desplegar.
- Pruebas de aceptación con Paula (diciembre) y **pr01**.
- Siguen abiertos: instalar el cron, capturas y vencimientos pasados en
  «Pendiente».

---

## Miércoles 7 de octubre de 2026 — pr01: endurecimiento de seguridad (20 controles)

### Qué se hizo
Rama `feature/pr01-seguridad`, creada desde `main`, por aviso del usuario.
Primero se auditó qué cubría ya el proyecto; el estado de cada control está en
`documentacion/PR01_SEGURIDAD.md`.
- **Huecos encontrados y cerrados:**
  - En desarrollo, cualquier archivo de `media/` (cuentas de cobro,
    certificados, adjuntos) se abría por dirección sin iniciar sesión. Ahora
    los archivos subidos pasan por una vista con sesión que solo entrega fotos,
    firmas y membrete a quien corresponde.
  - La contraseña de desarrollo de la administradora estaba escrita en
    `AGENTS.md`; se retiró y una prueba impide que vuelva a pasar.
  - Un archivo con la extensión cambiada (un programa renombrado como `.pdf`)
    se aceptaba; ahora se comprueba el contenido.
  - El bloqueo por fuerza bruta no dejaba registro.
- **Agregado:** política de seguridad de contenido y demás cabeceras en todos
  los entornos; huella de integridad en lo que viene del CDN; cookies de sesión
  `HttpOnly`/`SameSite`, con vencimiento a las 8 horas y al cerrar el
  navegador; campo señuelo contra robots, `robots.txt` y `X-Robots-Tag`; tope
  de peticiones en la API y en el enlace público del PDF; registro de consultas
  lentas y de eventos de seguridad; producción que no arranca con secretos de
  desarrollo ni con el superusuario de la base de datos; scripts de roles
  mínimos y de RLS para Supabase; Dependabot y flujo de GitHub Actions.
- Mientras tanto se instaló el cron (`scripts/instalar_cron.sh`) por aviso del
  usuario.

### Cómo verificarlo (entorno local)
Sin iniciar sesión, abrir `http://127.0.0.1:8000/media/` seguido de la ruta de
cualquier archivo: lleva al inicio de sesión. En las herramientas del
navegador, cualquier respuesta trae `Content-Security-Policy`. Cerrar y abrir el
navegador: pide iniciar sesión de nuevo.

### Resultado de las pruebas
`pruebas/seguridad/test_pr01.py` (55 pruebas). El script de RLS se probó en una
base temporal con las 42 tablas. El inicio de sesión se abrió en un navegador
real: carga completo con la CSP y las huellas, sin bloqueos.

**Revisión en navegador con sesión (11 de octubre de 2026).** Se abrieron en
Chrome, con la sesión de la administradora, el panel, las entradas del menú,
varios detalles y los seis reportes (36 pantallas): ninguna carga bloqueada por
la CSP, y los cuatro gráficos (dos del panel, cartera e ingresos) se pintan.
De paso se corrigió un error del Módulo 5 que no tenía que ver con la CSP: al
editar un hallazgo, las dos fechas del período salían vacías, porque el campo
no las entregaba en el formato año-mes-día que exige el navegador.

**Ensayo del despliegue (11 de octubre de 2026).** Como aún no hay proyecto de
Supabase, se ensayó la secuencia completa en un PostgreSQL temporal que lo
imita (`postgres` sin superusuario, roles `anon` y `authenticated`). Los
scripts 03 y 04 fallaban ahí: `postgres` no podía dar privilegios ni activar
RLS sobre las tablas de `contanika_dueno`. Corregido en el script 03; con eso
quedan las 53 tablas con RLS, el sistema funciona con `contanika_app` y
`check --deploy` no deja avisos. Producción ahora rechaza también el usuario
`postgres.<proyecto>` del pooler de Supabase.

### Pendientes
- **Del usuario:** cambiar la contraseña local de la administradora (quedó en
  el historial de Git, repositorio privado) y decidir si quiere CAPTCHA.
- **Al desplegar:** los seis pasos del final de `PR01_SEGURIDAD.md` (secretos
  nuevos, script de roles, script de RLS, `check --deploy`), ya ensayados.
  Falta el proyecto de Supabase y el servidor donde correrá el sistema.
- Mejora futura: pasar los scripts en línea a archivos para quitar
  `'unsafe-inline'` de la CSP.
