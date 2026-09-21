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
