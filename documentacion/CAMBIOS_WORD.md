# Cambios por llevar al documento Word — Contanika

Lista de lo que el sistema construido ya no coincide con `Contanika_Fases1y2_v11.docx`.
Corte: 6 de octubre de 2026. Marque cada punto al pasarlo al Word.

## 1. Stack y requisitos no funcionales

- [ ] **D1 y RQNF002:** donde dice «Django 4.2 LTS» debe decir «Django 5.2 LTS». Motivo: la serie 4.2
  terminó su soporte en abril de 2026 y `pip-audit` reportó 7 vulnerabilidades sin parche; la 5.2 tiene
  soporte de seguridad hasta abril de 2028.
- [ ] **PostgreSQL:** el entorno local corre PostgreSQL 16. Revisar la versión que cita el Word y dejar
  «PostgreSQL 16 local / Supabase en producción».

## 2. Diccionario de datos (numeral 2.5)

El Word documenta 36 tablas; el sistema tiene **42**.

### 2.1 Tablas nuevas

- [ ] **`obligacion_tributaria`** (Módulo 1): catálogo de obligaciones o vencimientos que pueden
  aplicarle a un cliente (10 sembradas).

  | Columna | Tipo | Nulo | Clave |
  |---|---|---|---|
  | id_obligacion | integer | No | PK |
  | nombre | varchar(60) | No | |
  | ambito | varchar(20) | No | |

- [ ] **`cliente_obligacion`** (Módulo 1): qué obligaciones presenta cada cliente; con ellas se calculan
  sus vencimientos.

  | Columna | Tipo | Nulo | Clave |
  |---|---|---|---|
  | id_cliente_obligacion | integer | No | PK |
  | id_cliente | integer | No | FK → cliente |
  | id_obligacion | integer | No | FK → obligacion_tributaria |

- [ ] **`honorario_servicio`** (Módulo 6, HU044): monto por tipo de servicio cuando el honorario es
  «Por servicio»; `honorario.monto` pasa a ser la suma.

  | Columna | Tipo | Nulo | Clave |
  |---|---|---|---|
  | id_honorario_servicio | integer | No | PK |
  | id_honorario | integer | No | FK → honorario |
  | id_tipo_servicio | integer | No | FK → tipo_servicio |
  | monto | numeric(12,2) | No | |

- [ ] **`configuracion_cobro`** (Módulo 6, ampliación de alcance): una sola fila con los parámetros del
  cobro mensual y los recordatorios automáticos.

  | Columna | Tipo | Nulo | Clave |
  |---|---|---|---|
  | id_configuracion_cobro | integer | No | PK |
  | cobro_automatico_activo | boolean | No | |
  | dia_generacion | smallint | No | |
  | dias_plazo_pago | smallint | No | |
  | canal_cobro | varchar(10) | No | |
  | id_cuenta_bancaria | integer | Sí | FK → cuenta_bancaria |
  | id_metodo_pago | integer | Sí | FK → metodo_pago |
  | recordatorios_activos | boolean | No | |
  | dias_antes_vencimiento | smallint | No | |
  | frecuencia_mora_dias | smallint | No | |
  | canal_recordatorio | varchar(10) | No | |
  | ultima_ejecucion | timestamp con zona | Sí | |

- [ ] **`envio_programado`** (Módulo 6, ampliación de alcance): cada envío de una cuenta de cobro o de
  un recordatorio, inmediato o programado, con su resultado.

  | Columna | Tipo | Nulo | Clave |
  |---|---|---|---|
  | id_envio_programado | integer | No | PK |
  | id_cuenta_cobro | integer | No | FK → cuenta_cobro |
  | tipo | varchar(20) | No | |
  | canal | varchar(10) | No | |
  | fecha_programada | timestamp con zona | No | |
  | estado | varchar(20) | No | |
  | id_usuario | integer | Sí | FK → usuario |
  | fecha_procesado | timestamp con zona | Sí | |
  | id_comunicacion | integer | Sí | FK → comunicacion |
  | detalle_error | varchar(255) | No | |

- [ ] **`descarga_reporte`** (Módulo 10, HU028-5): quién descargó cada reporte, cuándo, en qué formato
  y con qué filtros.

  | Columna | Tipo | Nulo | Clave |
  |---|---|---|---|
  | id_descarga | integer | No | PK |
  | id_reporte | integer | No | FK → reporte |
  | id_usuario | integer | No | FK → usuario |
  | formato | varchar(10) | No | |
  | filtros | text | No | |
  | fecha_hora | timestamp con zona | No | |

### 2.2 Columnas nuevas o que cambiaron

- [ ] **`usuario`:** tres columnas estándar de Django (`is_staff`, `is_superuser`, `last_login`), por
  usar un modelo de usuario propio sobre `AbstractBaseUser` (decisión T1). `foto_url` pasa a `foto`
  (archivo de imagen); `firma` también es un archivo de imagen.
- [ ] **`anotacion`:** columna nueva `fecha` (date, editable, por defecto hoy): fecha del hecho anotado.
  `fecha_hora` sigue siendo el registro exacto y automático.
- [ ] **`comunicacion`:** `canal` es de selección abierta (acepta valores nuevos); `fecha_hora` deja de
  ser automática para que el registro manual indique cuándo ocurrió el contacto.
- [ ] **`honorario`:** columnas nuevas `id_usuario_actualizacion` y `fecha_actualizacion` (HU044,
  criterio 4).
- [ ] **`cuenta_cobro`:** `archivo_url` pasa a `archivo` (PDF guardado); columnas nuevas
  `fecha_inicio_periodo` y `fecha_fin_periodo`.
- [ ] **`configuracion_alerta`:** columna nueva `fecha_envio` (date): día en que se envió la alerta,
  para no repetirla (HU040).
- [ ] **`adjunto`:** `archivo_url` pasa a `archivo` (archivo subido).
- [ ] **`configuracion_despacho`:** `membrete_url` pasa a `membrete` (imagen subida).
- [ ] **`documento`:** `archivo` es el PDF generado y guardado.

Los tipos exactos de todas las columnas están en `scripts/bd/01_esquema_contanika.sql`.

### 2.3 Disparadores

- [ ] Documentar los tres disparadores de la tabla `abono` (exigencia de la guía SENA: al menos uno):
  - `trg_abono_calcular_saldo` (BEFORE INSERT): bloquea la cuenta, fija `saldo_anterior` y
    `saldo_resultante` y rechaza montos menores o iguales a cero o mayores que el saldo.
  - `trg_abono_actualizar_estado` (AFTER INSERT): deja la cuenta en Abonada, Pagada o Vencida.
  - `trg_abono_inmutable` (BEFORE UPDATE OR DELETE): impide modificar o borrar un abono.

## 3. Alcance

- [ ] **Módulo 6, ampliación (25-sep-2026):** además de lo especificado incluye programación de envíos,
  cobro mensual automático y recordatorios automáticos de pago, con envío masivo y bandeja de WhatsApp
  pendientes.
- [ ] **Decisión T2 (WhatsApp):** correo por SMTP y WhatsApp por enlace `wa.me` con registro en
  Comunicaciones. La API de WhatsApp Business queda como mejora futura.
- [ ] **Decisión T3 (alertas):** comandos `procesar_cobros` (cada 15 minutos) y `procesar_alertas`
  (cada hora) ejecutados por cron.

## 4. Historias de usuario que cambiaron por decisión

- [ ] **Contador Junior (1-oct-2026):** consulta todos los clientes y los crea o edita, sin reasignar
  responsable ni cambiar el estado, sin inactivar ni importar. Lee hallazgos, documentos, expediente y
  comunicaciones de todos los clientes, pero solo escribe en los asignados. Credenciales, finanzas y
  reportes: solo de sus clientes. Afecta las HU de los módulos 1, 2, 3, 4, 5, 7 y 9 que lo limitaban a
  sus clientes asignados.
- [ ] **HU015 (hallazgos):** el Contador Junior no solo consulta: registra y gestiona los hallazgos de
  sus clientes asignados; no elimina.
- [ ] **HU026 (expediente):** bitácora inmutable. No hay edición ni eliminación; el Administrador
  archiva o restaura, y las archivadas se consultan con un filtro.
- [ ] **HU019 a HU021 (comunicaciones):** «Automática» es la que registra el sistema al enviar un correo
  o WhatsApp, aunque lo dispare una persona; «Manual» es el contacto anotado a mano.
- [ ] **HU022 (usuarios):** siempre queda al menos un Administrador activo; crear otro exige
  confirmación; un usuario solo se elimina si no tiene historial, de lo contrario se inactiva. El
  usuario nuevo recibe un correo con su acceso.
- [ ] **HU028 (reportes):** el reporte de credenciales sigue en el Módulo 1, solo en pantalla y sin
  descarga; hay uno por cliente y uno consolidado.
- [ ] **HU040 (alertas):** correo automático al responsable, notificación interna en la campana de la
  barra superior y WhatsApp como enlace que una persona envía.
- [ ] **Módulo 3 (notificaciones de tareas):** se calculan del historial de cambios de los últimos
  7 días; no hay tabla de notificaciones ni estado leído/no leído.
- [ ] **HU053 (ayuda):** además de la guía de módulos, preguntas frecuentes y contacto, incluye guías
  paso a paso de cada proceso, visibles según el rol.
- [ ] **Módulo 4:** la séptima plantilla sigue sin definir; el Administrador la crea desde «Gestión de
  plantillas».

## 5. Entregables de la Fase 3

- [ ] **3.1 Código de la base de datos:** `scripts/bd/01_esquema_contanika.sql` (42 tablas) y
  `scripts/bd/02_datos_iniciales.sql`.
- [ ] **3.3 Mapa de navegación:** `documentacion/MAPA_NAVEGACION.md` (se genera con
  `python gestionar.py generar_mapa_navegacion`). Los diagramas están en Mermaid: para pegarlos en el
  Word, ábralos en un visor de Mermaid y expórtelos como imagen.

## 6. Capturas pendientes

- [ ] Módulo 6: cartera, abonos y el rechazo del disparador visto en pgAdmin.
- [ ] Módulos 7, 8, 9 y 10.
- [ ] Panel principal (tablero gráfico).
- [ ] Ayuda: listado de guías y una guía abierta.
