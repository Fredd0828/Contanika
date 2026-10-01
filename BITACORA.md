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
