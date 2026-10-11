# Matriz CRUD y de seguridad — Contanika

Evidencia de la Fase 4 (pruebas y calidad). Corte: 7 de octubre de 2026.

Describe, por módulo, quién puede crear, consultar, actualizar y eliminar cada entidad, y cómo se
controla y se prueba cada riesgo de seguridad. El detalle ruta por ruta está en
[MAPA_NAVEGACION.md](MAPA_NAVEGACION.md), que se genera desde el código.

**Roles:** A = Administrador · S = Contador Senior · J = Contador Junior · — = nadie.

**Reglas que aplican a todas las matrices**

- Toda pantalla exige sesión iniciada.
- El Administrador activa o desactiva por rol cada módulo, el panel principal y cada reporte. Un módulo
  inhabilitado bloquea todas sus operaciones para ese rol, aunque la matriz diga que el rol puede.
- Clientes, vencimientos y tareas los consulta completo todo el equipo. Lo que cambia por rol es quién
  modifica.
- «J (sus clientes)» significa los clientes que el Junior tiene asignados como responsable.

## 1. Matriz CRUD por módulo

### Módulo 1 — Clientes

| Entidad | Crear | Consultar | Actualizar | Eliminar |
|---|---|---|---|---|
| Cliente | A · S · J | A · S · J (todos) | A · S · J | — (se inactiva: A · S) |
| Municipios, servicios y obligaciones del cliente | A · S · J | A · S · J | A · S · J | A · S · J |
| Credencial de portal | A · S | A · S · J (sus clientes) | A · S | A · S |
| Importación desde Excel | A · S | — | — | — |

- El Junior crea y edita clientes, pero no reasigna el responsable ni cambia el estado; el cliente
  nuevo queda a su nombre.
- Un cliente no se elimina: se inactiva y conserva su historial.
- Las contraseñas de las credenciales se guardan cifradas y se muestran enmascaradas.

### Módulo 2 — Calendario

| Entidad | Crear | Consultar | Actualizar | Eliminar |
|---|---|---|---|---|
| Vencimiento | A · S (manual y cálculo DIAN) | A · S · J (todos) | A · S | — |
| Estado de presentación del vencimiento | — | A · S · J | A · S · J (sus clientes o los que tiene como responsable) | — |
| Validación del vencimiento DIAN | — | A · S · J | A · S | — |
| Alerta de vencimiento | A · S | A · S · J | — | A · S |
| Anotación del calendario | A · S · J | Según la visibilidad que elige el autor | — | Autor o A |
| Tabla de referencia DIAN | A (fila a fila o desde Excel) | A | — | — |

- La fecha de un vencimiento siempre se puede editar, aunque la haya calculado el sistema.
- Recalcular no pisa un vencimiento ya validado.

### Módulo 3 — Tareas

| Entidad | Crear | Consultar | Actualizar | Eliminar |
|---|---|---|---|---|
| Tarea | A · S | A · S · J (todas) | A · S | A · S |
| Estado de la tarea | — | A · S · J | A · S · J (solo las asignadas a él) | — |
| Observación de avance | A · S · J (solo en las asignadas a él) | A · S · J | — | — |
| Historial de cambios | Automático | A · S · J | — | — |

### Módulo 4 — Documentos y certificados

| Entidad | Crear | Consultar | Actualizar | Eliminar |
|---|---|---|---|---|
| Documento generado | A · S · J (sus clientes) | A · S · J (todos) | — | A · S |
| Plantilla y sus campos | A | A | A | — |
| Firma y tarjeta profesional propias | A · S | A · S | A · S | — |
| Datos y membrete del despacho | A | A | A | — |

- Un documento generado no se edita: se genera uno nuevo.

### Módulo 5 — Hallazgos y revisiones

| Entidad | Crear | Consultar | Actualizar | Eliminar |
|---|---|---|---|---|
| Hallazgo | A · S · J (sus clientes) | A · S · J (todos) | A · S · J (sus clientes) | A · S |
| Estado del hallazgo | — | A · S · J | A · S · J (sus clientes) | — |
| Adjunto de soporte | A · S · J (sus clientes) | A · S · J | — | A · S · J (sus clientes) |

- Cerrar un hallazgo exige la observación de cierre.

### Módulo 6 — Honorarios, cartera y cuentas de cobro

| Entidad | Crear | Consultar | Actualizar | Eliminar |
|---|---|---|---|---|
| Honorario del cliente | A | A · S y J (sus clientes) | A | — |
| Cuenta de cobro | A (y el cobro automático) | A · S y J (sus clientes) | — | A (solo sin abonos) |
| Abono | A | A · S y J (sus clientes) | — | — |
| Envío de cuenta o recordatorio | A | A | A (reintentar, cancelar) | — |
| Catálogos (conceptos, cuentas bancarias, métodos de pago) | A | A | A | A (si no están en uso) |
| Configuración del cobro automático | — | A | A | — |
| Cartera | — | A · S y J (sus clientes) | — | — |

- Un abono no se modifica ni se borra: lo impide un disparador de la base de datos, que además calcula
  el saldo y el estado de la cuenta.
- El cliente abre el PDF de su cuenta por un enlace firmado que vence a los 30 días, sin iniciar sesión.

### Módulo 7 — Comunicaciones

| Entidad | Crear | Consultar | Actualizar | Eliminar |
|---|---|---|---|---|
| Comunicación manual (llamada, reunión) | A · S | A · S · J | — | — |
| Comunicación automática (correo, WhatsApp) | El sistema | A · S · J | — | — |

### Módulo 8 — Equipo y roles

| Entidad | Crear | Consultar | Actualizar | Eliminar |
|---|---|---|---|---|
| Usuario | A | A | A (datos, rol, estado, contraseña temporal) | A (solo sin historial) |
| Módulos y secciones por rol | — | A | A | — |
| Panel de trabajo del equipo | — | A · S | — | — |
| Perfil propio y contraseña | — | A · S · J | A · S · J | — |

- Siempre queda al menos un Administrador activo. Nadie se inactiva ni se elimina a sí mismo.
- El Administrador no puede quitarse el módulo de Equipo y roles.

### Módulo 9 — Expediente y bitácora

| Entidad | Crear | Consultar | Actualizar | Eliminar |
|---|---|---|---|---|
| Anotación | A · S · J (sus clientes) | A · S · J (todos) | — | — (se archiva o restaura: A) |
| Archivo de soporte | A · S · J (al crear la anotación) | A · S · J | — | — |

- La bitácora es inmutable: no hay edición ni eliminación.

### Módulo 10 — Reportes

| Entidad | Crear | Consultar | Actualizar | Eliminar |
|---|---|---|---|---|
| Reportes de clientes, vencimientos y tareas | — | A · S · J (todo el despacho) | — | — |
| Reportes de cartera y cuentas de cobro | — | A · S y J (sus clientes) | — | — |
| Reporte de ingresos mensuales | — | Roles con el reporte habilitado (consolidado) | — | — |
| Visibilidad de cada reporte por rol | — | A | A | — |
| Historial de descargas | Automático | A | — | — |

- Valor inicial: el Junior no tiene habilitados los reportes de cartera, cuentas de cobro e ingresos.

## 2. Matriz de seguridad

Las cuatro primeras filas se prueban sobre **todas las rutas del sistema** en
`pruebas/seguridad/test_seguridad_transversal.py`, que las toma del mismo recorrido que genera el mapa
de navegación: una ruta nueva queda cubierta sin escribir su prueba.

| Riesgo | Control | Dónde se prueba |
|---|---|---|
| Acceso sin sesión | `LoginRequiredMixin` en todas las vistas; redirige al inicio de sesión | `test_seguridad_transversal.py` (todas las rutas) |
| Acción de un rol sin permiso | `RolRequeridoMixin` con `roles_permitidos`; responde 403 | `test_seguridad_transversal.py` (cada ruta restringida, con cada rol no permitido) |
| Módulo inhabilitado para el rol | `ModuloHabilitadoMixin`; desaparece del menú, de la ficha y del panel, y la URL responde 403 | `test_seguridad_transversal.py` (todas las rutas de cada módulo), `test_panel.py` |
| CSRF | Token en todos los formularios POST | `test_seguridad_transversal.py` (todas las rutas que reciben POST) |
| Reporte oculto para el rol | `PermisoReporteRol`; no aparece ni abre por URL (403) | `pruebas/reportes/test_vistas.py` |
| Modificar datos de un cliente ajeno (Junior) | Selectores de escritura por cliente asignado; el formulario no ofrece clientes ajenos | Pruebas de selectores, formularios y vistas de documentos, hallazgos y expediente |
| Mover o comentar una tarea ajena (Junior) | `puede_actualizar_tarea` y validación en el servicio | `pruebas/tareas/test_vistas.py`, `test_servicios.py` |
| Ver finanzas de clientes ajenos | Selectores de finanzas restringidos a clientes asignados | `pruebas/finanzas/test_selectores.py`, `test_vistas.py` |
| Contraseñas de usuarios | Hash de Django y validadores de contraseña; nunca en texto plano | `pruebas/seguridad/test_modelos.py`, `test_equipo_servicios.py` |
| Credenciales de portales de clientes | Cifrado Fernet y vista enmascarada | `pruebas/clientes/test_credenciales.py` |
| Fuerza bruta en el inicio de sesión | django-axes: bloqueo tras 5 intentos fallidos, durante 1 hora | `test_seguridad_transversal.py` |
| XSS | Escape automático de las plantillas; datos de gráficos con `json_script` | `test_vistas.py` de calendario, tareas, documentos, expediente y reportes; `test_ayuda.py` |
| Inyección SQL | Solo ORM, sin SQL concatenado | `test_vistas.py` de expediente y comunicaciones |
| Archivos subidos | Validación de formato y tamaño (máximo 10 MB) | `pruebas/hallazgos`, `pruebas/expediente` |
| Alterar saldos o abonos | Disparadores de PostgreSQL sobre `abono` | `pruebas/finanzas/test_abonos.py` |
| Borrar historial | Bitácora y comunicaciones sin rutas de edición ni eliminación; usuarios con historial no se eliminan | `pruebas/expediente`, `pruebas/comunicaciones`, `pruebas/seguridad/test_equipo_servicios.py` |
| Enlace público del PDF | Enlace firmado con vencimiento a 30 días; es la única ruta pública además del inicio de sesión | `pruebas/finanzas/test_vistas_envios.py`, `test_envios.py`, `test_seguridad_transversal.py` |
| Datos personales (Ley 1581) | Acceso por sesión y rol; credenciales cifradas; descargas registradas | `pruebas/reportes/test_vistas.py` |

El endurecimiento posterior (cabeceras, política de contenido, archivos protegidos, cookies, robots,
límite de peticiones, monitoreo de consultas, secretos y scripts de la base de datos) está descrito
control por control en [PR01_SEGURIDAD.md](PR01_SEGURIDAD.md) y se prueba en
`pruebas/seguridad/test_pr01.py`.

## 3. Resultado del pase de calidad

Se completa con cada pase (`bash scripts/calidad.sh`).

| Verificación | Resultado al 7-oct-2026 |
|---|---|
| Pruebas automatizadas | 1225 pruebas, todas en verde |
| Cobertura | 96 % del código de `aplicaciones` (meta: 70 % por módulo y 85 % en servicios críticos); el archivo más bajo está en 77 % |
| `ruff` (estilo y formato) | Sin hallazgos |
| `bandit` (seguridad del código) | Sin hallazgos |
| `pip-audit` (dependencias) | Sin vulnerabilidades conocidas |
| `check` | Sin errores |
| `check --deploy` con la configuración de producción | Un aviso: la `SECRET_KEY` es la de desarrollo. Hay que generar una larga y aleatoria en el `.env` del servidor antes de desplegar |

## 4. Pendiente de la Fase 4

- Pruebas de aceptación con Paula Andrea (diciembre).
- De «pr01»: los pasos que se aplican en el servidor al desplegar (roles de base de datos, RLS, secretos nuevos y HTTPS).
