-- ============================================================================
-- Sistema de Información Contanika - Script de base de datos (entregable 3.1)
-- Empresa: Befrec Y Asociados SAS - Bogotá D.C.
-- Motor: PostgreSQL (16 local, compatible con PostgreSQL 15 de Supabase)
-- Generado desde las migraciones de Django 5.2 LTS el 21 de septiembre de 2026.
--
-- Contiene las 39 tablas del modelo relacional: las 36 del diccionario de
-- datos más honorario_servicio, configuracion_cobro y envio_programado,
-- agregadas en el Módulo 6 (numerales 2.4 y 2.5 del
-- documento de proyecto) y los comentarios de cada tabla tomados del
-- diccionario de datos. Las llaves foráneas se agregan al final del script.
-- Incluye el disparador exigido por la guía: sobre la tabla abono, calcula el
-- saldo anterior y resultante, actualiza el estado de pago de la cuenta de
-- cobro e impide modificar o eliminar abonos (migración finanzas 0004).
-- ============================================================================

-- Comentarios de las tablas (diccionario de datos, numeral 2.5)

COMMENT ON TABLE rol IS 'Roles del sistema: Administrador, Contador Senior, Contador Junior.';
COMMENT ON TABLE usuario IS 'Miembro del equipo del despacho (o el contador independiente).';
COMMENT ON TABLE modulo IS 'Catálogo de los 10 módulos del sistema.';
COMMENT ON TABLE permiso_rol_modulo IS 'Habilitación de cada módulo por rol (RQF031).';
COMMENT ON TABLE cliente IS 'Ficha central de cada cliente del despacho.';
COMMENT ON TABLE cliente_municipio IS 'Municipios o distritos adicionales donde el cliente tributa (multi-ICA).';
COMMENT ON TABLE tipo_servicio IS 'Catálogo de tipos de servicio contable prestado.';
COMMENT ON TABLE cliente_servicio IS 'Relación N:M entre cliente y los tipos de servicio que recibe.';
COMMENT ON TABLE credencial IS 'Credenciales de acceso a portales del cliente.';
COMMENT ON TABLE tabla_referencia_dian IS 'Calendario oficial DIAN por grupo de NIT, cargado por el Administrador.';
COMMENT ON TABLE vencimiento IS 'Vencimiento tributario nacional, distrital/municipal o de tarea marcada.';
COMMENT ON TABLE configuracion_alerta IS 'Alertas automáticas configuradas para un vencimiento.';
COMMENT ON TABLE anotacion_calendario IS 'Anotación libre por fecha, no asociada a un cliente.';
COMMENT ON TABLE anotacion_calendario_destinatario IS 'Usuarios etiquetados cuando la visibilidad es restringida.';
COMMENT ON TABLE tarea IS 'Tarjeta del tablero Kanban.';
COMMENT ON TABLE historial_tarea IS 'Registro de cada cambio de estado de una tarea.';
COMMENT ON TABLE observacion_tarea IS 'Observación de avance registrada sobre una tarea.';
COMMENT ON TABLE plantilla IS 'Plantilla de documento o certificado (6 base + creadas por el Administrador).';
COMMENT ON TABLE campo_plantilla IS 'Campo variable propio de cada plantilla (simple o repetible).';
COMMENT ON TABLE documento IS 'Documento o certificado generado para un cliente.';
COMMENT ON TABLE documento_valor IS 'Valor de un campo simple para un documento generado.';
COMMENT ON TABLE documento_detalle IS 'Fila de un campo repetible (ej. cada accionista) para un documento.';
COMMENT ON TABLE hallazgo IS 'Hallazgo, revisión, observación o inconsistencia registrada para un cliente.';
COMMENT ON TABLE adjunto IS 'Archivo de soporte adjunto (tabla genérica reutilizada por hallazgo y anotación).';
COMMENT ON TABLE honorario IS 'Configuración del honorario de un cliente.';
COMMENT ON TABLE honorario_servicio IS 'Monto del honorario por cada tipo de servicio del cliente (HU044).';
COMMENT ON TABLE concepto_facturable IS 'Catálogo reutilizable de conceptos facturables.';
COMMENT ON TABLE cuenta_bancaria IS 'Cuenta bancaria del despacho, disponible como destino de pago.';
COMMENT ON TABLE metodo_pago IS 'Catálogo de métodos de pago aceptados.';
COMMENT ON TABLE cuenta_cobro IS 'Cuenta de cobro generada en PDF para un cliente.';
COMMENT ON TABLE configuracion_cobro IS 'Parámetros del cobro mensual automático y de los recordatorios automáticos (una fila).';
COMMENT ON TABLE envio_programado IS 'Envío de cuenta de cobro o recordatorio por correo o WhatsApp, inmediato o programado.';
COMMENT ON TABLE cuenta_cobro_detalle IS 'Línea de servicio descrita dentro de una cuenta de cobro.';
COMMENT ON TABLE abono IS 'Pago o abono registrado contra una cuenta de cobro.';
COMMENT ON TABLE comunicacion IS 'Comunicación automática o manual registrada con un cliente.';
COMMENT ON TABLE anotacion IS 'Anotación cronológica del expediente y bitácora del cliente.';
COMMENT ON TABLE reporte IS 'Catálogo de los 6 reportes del Módulo 10.';
COMMENT ON TABLE permiso_reporte_rol IS 'Habilitación de cada reporte individual por rol.';
COMMENT ON TABLE configuracion_despacho IS 'Datos fijos del despacho usados en documentos y cuentas de cobro.';

--
-- PostgreSQL database dump
--

\restrict vzljRXeDMnxgnYVzuunOG3e1a6aJXUxxLyENtAadYdWC2rZrrmUVasdwfysw6gw

-- Dumped from database version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: fn_abono_calcular_saldo(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE OR REPLACE FUNCTION public.fn_abono_calcular_saldo() RETURNS trigger AS $$
DECLARE
    v_valor_total numeric(12, 2);
    v_abonado numeric(12, 2);
BEGIN
    IF NEW.monto IS NULL OR NEW.monto <= 0 THEN
        RAISE EXCEPTION 'El monto del abono debe ser mayor que cero.'
            USING ERRCODE = 'check_violation';
    END IF;

    -- Bloquea la cuenta para que dos abonos simultáneos no calculen el mismo saldo.
    SELECT valor_total INTO v_valor_total
      FROM cuenta_cobro
     WHERE id_cuenta_cobro = NEW.id_cuenta_cobro
       FOR UPDATE;

    SELECT COALESCE(SUM(monto), 0) INTO v_abonado
      FROM abono
     WHERE id_cuenta_cobro = NEW.id_cuenta_cobro;

    NEW.saldo_anterior := v_valor_total - v_abonado;
    IF NEW.monto > NEW.saldo_anterior THEN
        RAISE EXCEPTION 'El abono supera el saldo pendiente de la cuenta (%).', NEW.saldo_anterior
            USING ERRCODE = 'check_violation';
    END IF;
    NEW.saldo_resultante := NEW.saldo_anterior - NEW.monto;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


--
-- Name: fn_abono_actualizar_estado_cuenta(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE OR REPLACE FUNCTION public.fn_abono_actualizar_estado_cuenta() RETURNS trigger AS $$
BEGIN
    UPDATE cuenta_cobro
       SET estado_pago = CASE
               WHEN NEW.saldo_resultante = 0 THEN 'Pagada'
               WHEN fecha_vencimiento_pago < (now() AT TIME ZONE 'America/Bogota')::date THEN 'Vencida'
               ELSE 'Abonada'
           END
     WHERE id_cuenta_cobro = NEW.id_cuenta_cobro;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


--
-- Name: fn_abono_inmutable(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE OR REPLACE FUNCTION public.fn_abono_inmutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Los abonos no se modifican ni se eliminan: conservan la trazabilidad de la cartera.'
        USING ERRCODE = 'restrict_violation';
END;
$$ LANGUAGE plpgsql;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: abono; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.abono (
    id_abono integer NOT NULL,
    fecha date NOT NULL,
    monto numeric(12,2) NOT NULL,
    saldo_anterior numeric(12,2) NOT NULL,
    saldo_resultante numeric(12,2) NOT NULL,
    id_cuenta_cobro integer NOT NULL,
    id_metodo_pago integer,
    id_usuario_responsable integer NOT NULL
);


--
-- Name: abono_id_abono_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.abono ALTER COLUMN id_abono ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.abono_id_abono_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: adjunto; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.adjunto (
    id_adjunto integer NOT NULL,
    tabla_origen character varying(30) NOT NULL,
    id_origen integer NOT NULL,
    nombre_archivo character varying(150) NOT NULL,
    fecha_carga timestamp with time zone NOT NULL,
    archivo character varying(255) NOT NULL,
    CONSTRAINT adjunto_id_origen_check CHECK ((id_origen >= 0))
);


--
-- Name: adjunto_id_adjunto_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.adjunto ALTER COLUMN id_adjunto ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.adjunto_id_adjunto_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: anotacion; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.anotacion (
    id_anotacion integer NOT NULL,
    tipo_anotacion character varying(40) NOT NULL,
    fecha_hora timestamp with time zone NOT NULL,
    contenido text NOT NULL,
    archivado boolean NOT NULL,
    id_cliente integer NOT NULL,
    id_usuario integer NOT NULL
);


--
-- Name: anotacion_calendario; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.anotacion_calendario (
    id_anotacion_cal integer NOT NULL,
    fecha date NOT NULL,
    contenido text NOT NULL,
    visibilidad character varying(20) NOT NULL,
    id_usuario_autor integer NOT NULL
);


--
-- Name: anotacion_calendario_destinatario; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.anotacion_calendario_destinatario (
    id_destinatario integer NOT NULL,
    id_anotacion_cal integer NOT NULL,
    id_usuario integer NOT NULL
);


--
-- Name: anotacion_calendario_destinatario_id_destinatario_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.anotacion_calendario_destinatario ALTER COLUMN id_destinatario ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.anotacion_calendario_destinatario_id_destinatario_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: anotacion_calendario_id_anotacion_cal_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.anotacion_calendario ALTER COLUMN id_anotacion_cal ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.anotacion_calendario_id_anotacion_cal_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: anotacion_id_anotacion_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.anotacion ALTER COLUMN id_anotacion ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.anotacion_id_anotacion_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: campo_plantilla; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.campo_plantilla (
    id_campo integer NOT NULL,
    nombre_campo character varying(80) NOT NULL,
    tipo_campo character varying(20) NOT NULL,
    es_repetible boolean NOT NULL,
    id_plantilla integer NOT NULL
);


--
-- Name: campo_plantilla_id_campo_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.campo_plantilla ALTER COLUMN id_campo ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.campo_plantilla_id_campo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: cliente; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cliente (
    id_cliente integer NOT NULL,
    nombre_razon_social character varying(200) NOT NULL,
    nit_cedula character varying(10) NOT NULL,
    tipo_documento character varying(15) NOT NULL,
    tipo_persona character varying(10) NOT NULL,
    regimen_tributario character varying(40) NOT NULL,
    responsable_iva boolean NOT NULL,
    ciudad character varying(60) NOT NULL,
    municipio_principal character varying(60) NOT NULL,
    informacion_contacto character varying(200) NOT NULL,
    correo_cliente character varying(200) NOT NULL,
    estado character varying(15) NOT NULL,
    fecha_registro date NOT NULL,
    id_usuario_responsable integer
);


--
-- Name: cliente_id_cliente_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.cliente ALTER COLUMN id_cliente ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.cliente_id_cliente_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: cliente_municipio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cliente_municipio (
    id_cliente_municipio integer NOT NULL,
    municipio character varying(60) NOT NULL,
    id_cliente integer NOT NULL
);


--
-- Name: cliente_municipio_id_cliente_municipio_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.cliente_municipio ALTER COLUMN id_cliente_municipio ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.cliente_municipio_id_cliente_municipio_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: cliente_servicio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cliente_servicio (
    id_cliente_servicio integer NOT NULL,
    id_cliente integer NOT NULL,
    id_tipo_servicio integer NOT NULL
);


--
-- Name: cliente_servicio_id_cliente_servicio_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.cliente_servicio ALTER COLUMN id_cliente_servicio ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.cliente_servicio_id_cliente_servicio_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: comunicacion; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.comunicacion (
    id_comunicacion integer NOT NULL,
    canal character varying(20) NOT NULL,
    tipo character varying(15) NOT NULL,
    contenido_resumen text NOT NULL,
    fecha_hora timestamp with time zone NOT NULL,
    estado_envio character varying(20) NOT NULL,
    numero_reintentos integer NOT NULL,
    modulo_origen character varying(30) NOT NULL,
    id_cliente integer NOT NULL,
    id_usuario integer,
    CONSTRAINT comunicacion_numero_reintentos_check CHECK ((numero_reintentos >= 0))
);


--
-- Name: comunicacion_id_comunicacion_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.comunicacion ALTER COLUMN id_comunicacion ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.comunicacion_id_comunicacion_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: concepto_facturable; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.concepto_facturable (
    id_concepto integer NOT NULL,
    nombre_concepto character varying(100) NOT NULL,
    valor_sugerido numeric(12,2) NOT NULL
);


--
-- Name: concepto_facturable_id_concepto_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.concepto_facturable ALTER COLUMN id_concepto ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.concepto_facturable_id_concepto_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: configuracion_alerta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.configuracion_alerta (
    id_alerta integer NOT NULL,
    dias_anticipacion integer NOT NULL,
    canal character varying(20) NOT NULL,
    id_vencimiento integer NOT NULL,
    CONSTRAINT configuracion_alerta_dias_anticipacion_check CHECK ((dias_anticipacion >= 0))
);


--
-- Name: configuracion_alerta_id_alerta_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.configuracion_alerta ALTER COLUMN id_alerta ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.configuracion_alerta_id_alerta_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: configuracion_cobro; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.configuracion_cobro (
    id_configuracion_cobro integer NOT NULL,
    cobro_automatico_activo boolean NOT NULL,
    dia_generacion smallint NOT NULL,
    dias_plazo_pago smallint NOT NULL,
    canal_cobro character varying(10) NOT NULL,
    recordatorios_activos boolean NOT NULL,
    dias_antes_vencimiento smallint NOT NULL,
    frecuencia_mora_dias smallint NOT NULL,
    canal_recordatorio character varying(10) NOT NULL,
    ultima_ejecucion timestamp with time zone,
    id_cuenta_bancaria integer,
    id_metodo_pago integer,
    CONSTRAINT configuracion_cobro_dia_generacion_check CHECK ((dia_generacion >= 0)),
    CONSTRAINT configuracion_cobro_dias_plazo_pago_check CHECK ((dias_plazo_pago >= 0)),
    CONSTRAINT configuracion_cobro_dias_antes_vencimiento_check CHECK ((dias_antes_vencimiento >= 0)),
    CONSTRAINT configuracion_cobro_frecuencia_mora_dias_check CHECK ((frecuencia_mora_dias >= 0))
);


--
-- Name: configuracion_cobro_id_configuracion_cobro_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.configuracion_cobro ALTER COLUMN id_configuracion_cobro ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.configuracion_cobro_id_configuracion_cobro_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: configuracion_despacho; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.configuracion_despacho (
    id_configuracion integer NOT NULL,
    nombre_despacho character varying(150) NOT NULL,
    nit_despacho character varying(20) NOT NULL,
    ciudad character varying(60) NOT NULL,
    direccion character varying(150) NOT NULL,
    telefono character varying(20) NOT NULL,
    correo character varying(100) NOT NULL,
    membrete character varying(100) NOT NULL
);


--
-- Name: configuracion_despacho_id_configuracion_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.configuracion_despacho ALTER COLUMN id_configuracion ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.configuracion_despacho_id_configuracion_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: credencial; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.credencial (
    id_credencial integer NOT NULL,
    concepto character varying(60) NOT NULL,
    usuario_acceso character varying(100) NOT NULL,
    clave_cifrada character varying(255) NOT NULL,
    fecha_creacion timestamp with time zone NOT NULL,
    fecha_ultima_actualizacion timestamp with time zone NOT NULL,
    id_cliente integer NOT NULL
);


--
-- Name: credencial_id_credencial_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.credencial ALTER COLUMN id_credencial ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.credencial_id_credencial_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: cuenta_bancaria; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cuenta_bancaria (
    id_cuenta_bancaria integer NOT NULL,
    banco character varying(60) NOT NULL,
    tipo_cuenta character varying(20) NOT NULL,
    numero_cuenta character varying(30) NOT NULL,
    titular character varying(150) NOT NULL
);


--
-- Name: cuenta_bancaria_id_cuenta_bancaria_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.cuenta_bancaria ALTER COLUMN id_cuenta_bancaria ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.cuenta_bancaria_id_cuenta_bancaria_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: cuenta_cobro; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cuenta_cobro (
    id_cuenta_cobro integer NOT NULL,
    periodo_facturado character varying(20) NOT NULL,
    valor_total numeric(12,2) NOT NULL,
    fecha_vencimiento_pago date NOT NULL,
    estado_envio character varying(20) NOT NULL,
    estado_pago character varying(20) NOT NULL,
    fecha_generacion timestamp with time zone NOT NULL,
    id_cliente integer NOT NULL,
    id_cuenta_bancaria integer,
    id_honorario integer,
    id_metodo_pago integer,
    archivo character varying(100) NOT NULL,
    fecha_fin_periodo date,
    fecha_inicio_periodo date
);


--
-- Name: cuenta_cobro_detalle; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cuenta_cobro_detalle (
    id_detalle_cobro integer NOT NULL,
    descripcion_linea character varying(200) NOT NULL,
    valor_linea numeric(12,2) NOT NULL,
    id_concepto integer,
    id_cuenta_cobro integer NOT NULL
);


--
-- Name: cuenta_cobro_detalle_id_detalle_cobro_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.cuenta_cobro_detalle ALTER COLUMN id_detalle_cobro ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.cuenta_cobro_detalle_id_detalle_cobro_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: cuenta_cobro_id_cuenta_cobro_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.cuenta_cobro ALTER COLUMN id_cuenta_cobro ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.cuenta_cobro_id_cuenta_cobro_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: documento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documento (
    id_documento integer NOT NULL,
    fecha_generacion timestamp with time zone NOT NULL,
    descripcion text NOT NULL,
    id_cliente integer NOT NULL,
    id_plantilla integer NOT NULL,
    id_usuario_generador integer NOT NULL,
    archivo character varying(255) NOT NULL,
    periodo character varying(60) NOT NULL
);


--
-- Name: documento_detalle; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documento_detalle (
    id_detalle integer NOT NULL,
    fila integer NOT NULL,
    valor text NOT NULL,
    id_campo integer NOT NULL,
    id_documento integer NOT NULL,
    CONSTRAINT documento_detalle_fila_check CHECK ((fila >= 0))
);


--
-- Name: documento_detalle_id_detalle_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.documento_detalle ALTER COLUMN id_detalle ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.documento_detalle_id_detalle_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: documento_id_documento_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.documento ALTER COLUMN id_documento ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.documento_id_documento_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: documento_valor; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documento_valor (
    id_valor integer NOT NULL,
    valor text NOT NULL,
    id_campo integer NOT NULL,
    id_documento integer NOT NULL
);


--
-- Name: documento_valor_id_valor_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.documento_valor ALTER COLUMN id_valor ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.documento_valor_id_valor_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: envio_programado; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.envio_programado (
    id_envio_programado integer NOT NULL,
    tipo character varying(20) NOT NULL,
    canal character varying(10) NOT NULL,
    fecha_programada timestamp with time zone NOT NULL,
    estado character varying(20) NOT NULL,
    fecha_procesado timestamp with time zone,
    detalle_error character varying(255) NOT NULL,
    id_comunicacion integer,
    id_cuenta_cobro integer NOT NULL,
    id_usuario integer
);


--
-- Name: envio_programado_id_envio_programado_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.envio_programado ALTER COLUMN id_envio_programado ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.envio_programado_id_envio_programado_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: hallazgo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hallazgo (
    id_hallazgo integer NOT NULL,
    tipo_hallazgo character varying(40) NOT NULL,
    fecha_inicio_periodo date NOT NULL,
    fecha_fin_periodo date NOT NULL,
    prioridad character varying(10) NOT NULL,
    descripcion text NOT NULL,
    estado character varying(20) NOT NULL,
    observacion_cierre text NOT NULL,
    id_cliente integer NOT NULL,
    id_usuario_responsable integer
);


--
-- Name: hallazgo_id_hallazgo_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.hallazgo ALTER COLUMN id_hallazgo ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.hallazgo_id_hallazgo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: historial_tarea; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.historial_tarea (
    id_historial integer NOT NULL,
    estado_anterior character varying(20) NOT NULL,
    estado_nuevo character varying(20) NOT NULL,
    fecha_cambio timestamp with time zone NOT NULL,
    id_tarea integer NOT NULL,
    id_usuario integer NOT NULL
);


--
-- Name: historial_tarea_id_historial_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.historial_tarea ALTER COLUMN id_historial ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.historial_tarea_id_historial_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: honorario; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.honorario (
    id_honorario integer NOT NULL,
    tipo character varying(20) NOT NULL,
    monto numeric(12,2) NOT NULL,
    id_cliente integer NOT NULL,
    fecha_actualizacion timestamp with time zone NOT NULL,
    id_usuario_actualizacion integer
);


--
-- Name: honorario_id_honorario_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.honorario ALTER COLUMN id_honorario ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.honorario_id_honorario_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: honorario_servicio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.honorario_servicio (
    id_honorario_servicio integer NOT NULL,
    monto numeric(12,2) NOT NULL,
    id_honorario integer NOT NULL,
    id_tipo_servicio integer NOT NULL
);


--
-- Name: honorario_servicio_id_honorario_servicio_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.honorario_servicio ALTER COLUMN id_honorario_servicio ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.honorario_servicio_id_honorario_servicio_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: metodo_pago; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metodo_pago (
    id_metodo_pago integer NOT NULL,
    nombre_metodo character varying(40) NOT NULL
);


--
-- Name: metodo_pago_id_metodo_pago_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.metodo_pago ALTER COLUMN id_metodo_pago ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.metodo_pago_id_metodo_pago_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: modulo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.modulo (
    id_modulo integer NOT NULL,
    nombre_modulo character varying(60) NOT NULL,
    codigo_modulo character varying(20) NOT NULL
);


--
-- Name: modulo_id_modulo_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.modulo ALTER COLUMN id_modulo ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.modulo_id_modulo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: observacion_tarea; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.observacion_tarea (
    id_observacion integer NOT NULL,
    contenido text NOT NULL,
    fecha timestamp with time zone NOT NULL,
    id_tarea integer NOT NULL,
    id_usuario integer NOT NULL
);


--
-- Name: observacion_tarea_id_observacion_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.observacion_tarea ALTER COLUMN id_observacion ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.observacion_tarea_id_observacion_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: permiso_reporte_rol; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permiso_reporte_rol (
    id_permiso_reporte integer NOT NULL,
    habilitado boolean NOT NULL,
    id_reporte integer NOT NULL,
    id_rol integer NOT NULL
);


--
-- Name: permiso_reporte_rol_id_permiso_reporte_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.permiso_reporte_rol ALTER COLUMN id_permiso_reporte ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.permiso_reporte_rol_id_permiso_reporte_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: permiso_rol_modulo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permiso_rol_modulo (
    id_permiso integer NOT NULL,
    habilitado boolean NOT NULL,
    id_modulo integer NOT NULL,
    id_rol integer NOT NULL
);


--
-- Name: permiso_rol_modulo_id_permiso_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.permiso_rol_modulo ALTER COLUMN id_permiso ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.permiso_rol_modulo_id_permiso_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: plantilla; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plantilla (
    id_plantilla integer NOT NULL,
    nombre_plantilla character varying(100) NOT NULL,
    texto_predeterminado text NOT NULL,
    tipo_documento character varying(60) NOT NULL
);


--
-- Name: plantilla_id_plantilla_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.plantilla ALTER COLUMN id_plantilla ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.plantilla_id_plantilla_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: reporte; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reporte (
    id_reporte integer NOT NULL,
    nombre_reporte character varying(60) NOT NULL,
    modulo_origen character varying(40) NOT NULL
);


--
-- Name: reporte_id_reporte_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.reporte ALTER COLUMN id_reporte ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.reporte_id_reporte_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: rol; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rol (
    id_rol integer NOT NULL,
    nombre_rol character varying(30) NOT NULL
);


--
-- Name: rol_id_rol_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.rol ALTER COLUMN id_rol ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.rol_id_rol_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tabla_referencia_dian; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tabla_referencia_dian (
    id_referencia integer NOT NULL,
    tipo_obligacion character varying(40) NOT NULL,
    grupo_nit character varying(10) NOT NULL,
    fecha_vencimiento date NOT NULL,
    periodo_gravable character varying(10) NOT NULL
);


--
-- Name: tabla_referencia_dian_id_referencia_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.tabla_referencia_dian ALTER COLUMN id_referencia ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.tabla_referencia_dian_id_referencia_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tarea; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tarea (
    id_tarea integer NOT NULL,
    titulo character varying(150) NOT NULL,
    descripcion text NOT NULL,
    tipo_tarea character varying(40) NOT NULL,
    prioridad character varying(10) NOT NULL,
    fecha_vencimiento date,
    estado character varying(20) NOT NULL,
    mostrar_en_calendario boolean NOT NULL,
    id_cliente integer NOT NULL,
    id_usuario_responsable integer
);


--
-- Name: tarea_id_tarea_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.tarea ALTER COLUMN id_tarea ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.tarea_id_tarea_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tipo_servicio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipo_servicio (
    id_tipo_servicio integer NOT NULL,
    nombre_servicio character varying(80) NOT NULL
);


--
-- Name: tipo_servicio_id_tipo_servicio_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.tipo_servicio ALTER COLUMN id_tipo_servicio ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.tipo_servicio_id_tipo_servicio_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: usuario; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuario (
    last_login timestamp with time zone,
    id_usuario integer NOT NULL,
    nombre character varying(150) NOT NULL,
    correo character varying(150) NOT NULL,
    telefono character varying(20) NOT NULL,
    foto_url character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    numero_tarjeta_profesional character varying(30) NOT NULL,
    estado character varying(15) NOT NULL,
    fecha_creacion timestamp with time zone NOT NULL,
    is_staff boolean NOT NULL,
    is_superuser boolean NOT NULL,
    id_rol integer NOT NULL,
    firma character varying(100) NOT NULL,
    identificacion character varying(20) NOT NULL
);


--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.usuario ALTER COLUMN id_usuario ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.usuario_id_usuario_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: vencimiento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vencimiento (
    id_vencimiento integer NOT NULL,
    tipo_obligacion character varying(40) NOT NULL,
    ambito character varying(20) NOT NULL,
    municipio character varying(60) NOT NULL,
    fecha_vencimiento date NOT NULL,
    estado_presentacion character varying(20) NOT NULL,
    estado_validacion character varying(20) NOT NULL,
    id_cliente integer NOT NULL,
    id_usuario_responsable integer,
    id_tarea integer
);


--
-- Name: vencimiento_id_vencimiento_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.vencimiento ALTER COLUMN id_vencimiento ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.vencimiento_id_vencimiento_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: abono abono_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.abono
    ADD CONSTRAINT abono_pkey PRIMARY KEY (id_abono);


--
-- Name: adjunto adjunto_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.adjunto
    ADD CONSTRAINT adjunto_pkey PRIMARY KEY (id_adjunto);


--
-- Name: anotacion_calendario_destinatario anotacion_calendario_destinatario_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anotacion_calendario_destinatario
    ADD CONSTRAINT anotacion_calendario_destinatario_pkey PRIMARY KEY (id_destinatario);


--
-- Name: anotacion_calendario anotacion_calendario_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anotacion_calendario
    ADD CONSTRAINT anotacion_calendario_pkey PRIMARY KEY (id_anotacion_cal);


--
-- Name: anotacion anotacion_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anotacion
    ADD CONSTRAINT anotacion_pkey PRIMARY KEY (id_anotacion);


--
-- Name: campo_plantilla campo_plantilla_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campo_plantilla
    ADD CONSTRAINT campo_plantilla_pkey PRIMARY KEY (id_campo);


--
-- Name: cliente_municipio cliente_municipio_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente_municipio
    ADD CONSTRAINT cliente_municipio_pkey PRIMARY KEY (id_cliente_municipio);


--
-- Name: cliente cliente_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_pkey PRIMARY KEY (id_cliente);


--
-- Name: cliente_servicio cliente_servicio_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente_servicio
    ADD CONSTRAINT cliente_servicio_pkey PRIMARY KEY (id_cliente_servicio);


--
-- Name: comunicacion comunicacion_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comunicacion
    ADD CONSTRAINT comunicacion_pkey PRIMARY KEY (id_comunicacion);


--
-- Name: concepto_facturable concepto_facturable_nombre_concepto_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concepto_facturable
    ADD CONSTRAINT concepto_facturable_nombre_concepto_key UNIQUE (nombre_concepto);


--
-- Name: concepto_facturable concepto_facturable_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concepto_facturable
    ADD CONSTRAINT concepto_facturable_pkey PRIMARY KEY (id_concepto);


--
-- Name: configuracion_alerta configuracion_alerta_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuracion_alerta
    ADD CONSTRAINT configuracion_alerta_pkey PRIMARY KEY (id_alerta);


--
-- Name: configuracion_cobro configuracion_cobro_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuracion_cobro
    ADD CONSTRAINT configuracion_cobro_pkey PRIMARY KEY (id_configuracion_cobro);


--
-- Name: configuracion_despacho configuracion_despacho_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuracion_despacho
    ADD CONSTRAINT configuracion_despacho_pkey PRIMARY KEY (id_configuracion);


--
-- Name: credencial credencial_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.credencial
    ADD CONSTRAINT credencial_pkey PRIMARY KEY (id_credencial);


--
-- Name: cuenta_bancaria cuenta_bancaria_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuenta_bancaria
    ADD CONSTRAINT cuenta_bancaria_pkey PRIMARY KEY (id_cuenta_bancaria);


--
-- Name: cuenta_cobro_detalle cuenta_cobro_detalle_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuenta_cobro_detalle
    ADD CONSTRAINT cuenta_cobro_detalle_pkey PRIMARY KEY (id_detalle_cobro);


--
-- Name: cuenta_cobro cuenta_cobro_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuenta_cobro
    ADD CONSTRAINT cuenta_cobro_pkey PRIMARY KEY (id_cuenta_cobro);


--
-- Name: documento_detalle documento_detalle_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento_detalle
    ADD CONSTRAINT documento_detalle_pkey PRIMARY KEY (id_detalle);


--
-- Name: documento documento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento
    ADD CONSTRAINT documento_pkey PRIMARY KEY (id_documento);


--
-- Name: documento_valor documento_valor_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento_valor
    ADD CONSTRAINT documento_valor_pkey PRIMARY KEY (id_valor);


--
-- Name: envio_programado envio_programado_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envio_programado
    ADD CONSTRAINT envio_programado_pkey PRIMARY KEY (id_envio_programado);


--
-- Name: hallazgo hallazgo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hallazgo
    ADD CONSTRAINT hallazgo_pkey PRIMARY KEY (id_hallazgo);


--
-- Name: historial_tarea historial_tarea_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historial_tarea
    ADD CONSTRAINT historial_tarea_pkey PRIMARY KEY (id_historial);


--
-- Name: honorario honorario_id_cliente_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.honorario
    ADD CONSTRAINT honorario_id_cliente_key UNIQUE (id_cliente);


--
-- Name: honorario honorario_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.honorario
    ADD CONSTRAINT honorario_pkey PRIMARY KEY (id_honorario);


--
-- Name: honorario_servicio honorario_servicio_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.honorario_servicio
    ADD CONSTRAINT honorario_servicio_pkey PRIMARY KEY (id_honorario_servicio);


--
-- Name: honorario_servicio unico_honorario_servicio; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.honorario_servicio
    ADD CONSTRAINT unico_honorario_servicio UNIQUE (id_honorario, id_tipo_servicio);


--
-- Name: metodo_pago metodo_pago_nombre_metodo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metodo_pago
    ADD CONSTRAINT metodo_pago_nombre_metodo_key UNIQUE (nombre_metodo);


--
-- Name: metodo_pago metodo_pago_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metodo_pago
    ADD CONSTRAINT metodo_pago_pkey PRIMARY KEY (id_metodo_pago);


--
-- Name: modulo modulo_codigo_modulo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modulo
    ADD CONSTRAINT modulo_codigo_modulo_key UNIQUE (codigo_modulo);


--
-- Name: modulo modulo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modulo
    ADD CONSTRAINT modulo_pkey PRIMARY KEY (id_modulo);


--
-- Name: observacion_tarea observacion_tarea_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.observacion_tarea
    ADD CONSTRAINT observacion_tarea_pkey PRIMARY KEY (id_observacion);


--
-- Name: permiso_reporte_rol permiso_reporte_rol_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permiso_reporte_rol
    ADD CONSTRAINT permiso_reporte_rol_pkey PRIMARY KEY (id_permiso_reporte);


--
-- Name: permiso_rol_modulo permiso_rol_modulo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permiso_rol_modulo
    ADD CONSTRAINT permiso_rol_modulo_pkey PRIMARY KEY (id_permiso);


--
-- Name: plantilla plantilla_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plantilla
    ADD CONSTRAINT plantilla_pkey PRIMARY KEY (id_plantilla);


--
-- Name: reporte reporte_nombre_reporte_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reporte
    ADD CONSTRAINT reporte_nombre_reporte_key UNIQUE (nombre_reporte);


--
-- Name: reporte reporte_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reporte
    ADD CONSTRAINT reporte_pkey PRIMARY KEY (id_reporte);


--
-- Name: rol rol_nombre_rol_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_nombre_rol_key UNIQUE (nombre_rol);


--
-- Name: rol rol_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_pkey PRIMARY KEY (id_rol);


--
-- Name: tabla_referencia_dian tabla_referencia_dian_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tabla_referencia_dian
    ADD CONSTRAINT tabla_referencia_dian_pkey PRIMARY KEY (id_referencia);


--
-- Name: tarea tarea_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tarea
    ADD CONSTRAINT tarea_pkey PRIMARY KEY (id_tarea);


--
-- Name: tipo_servicio tipo_servicio_nombre_servicio_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_servicio
    ADD CONSTRAINT tipo_servicio_nombre_servicio_key UNIQUE (nombre_servicio);


--
-- Name: tipo_servicio tipo_servicio_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_servicio
    ADD CONSTRAINT tipo_servicio_pkey PRIMARY KEY (id_tipo_servicio);


--
-- Name: anotacion_calendario_destinatario unico_anotacion_destinatario; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anotacion_calendario_destinatario
    ADD CONSTRAINT unico_anotacion_destinatario UNIQUE (id_anotacion_cal, id_usuario);


--
-- Name: campo_plantilla unico_campo_plantilla; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campo_plantilla
    ADD CONSTRAINT unico_campo_plantilla UNIQUE (id_plantilla, nombre_campo);


--
-- Name: cliente_servicio unico_cliente_servicio; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente_servicio
    ADD CONSTRAINT unico_cliente_servicio UNIQUE (id_cliente, id_tipo_servicio);


--
-- Name: documento_valor unico_documento_campo; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento_valor
    ADD CONSTRAINT unico_documento_campo UNIQUE (id_documento, id_campo);


--
-- Name: tabla_referencia_dian unico_referencia_dian; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tabla_referencia_dian
    ADD CONSTRAINT unico_referencia_dian UNIQUE (tipo_obligacion, grupo_nit, periodo_gravable);


--
-- Name: permiso_reporte_rol unico_reporte_rol; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permiso_reporte_rol
    ADD CONSTRAINT unico_reporte_rol UNIQUE (id_reporte, id_rol);


--
-- Name: permiso_rol_modulo unico_rol_modulo; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permiso_rol_modulo
    ADD CONSTRAINT unico_rol_modulo UNIQUE (id_rol, id_modulo);


--
-- Name: usuario usuario_correo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_correo_key UNIQUE (correo);


--
-- Name: usuario usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id_usuario);


--
-- Name: vencimiento vencimiento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vencimiento
    ADD CONSTRAINT vencimiento_pkey PRIMARY KEY (id_vencimiento);


--
-- Name: abono_id_cuenta_cobro_7f49f5d6; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX abono_id_cuenta_cobro_7f49f5d6 ON public.abono USING btree (id_cuenta_cobro);


--
-- Name: abono_id_metodo_pago_7a0a104c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX abono_id_metodo_pago_7a0a104c ON public.abono USING btree (id_metodo_pago);


--
-- Name: abono_id_usuario_responsable_4125996e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX abono_id_usuario_responsable_4125996e ON public.abono USING btree (id_usuario_responsable);


--
-- Name: anotacion_calendario_destinatario_id_anotacion_cal_0c50ca98; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX anotacion_calendario_destinatario_id_anotacion_cal_0c50ca98 ON public.anotacion_calendario_destinatario USING btree (id_anotacion_cal);


--
-- Name: anotacion_calendario_destinatario_id_usuario_10833146; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX anotacion_calendario_destinatario_id_usuario_10833146 ON public.anotacion_calendario_destinatario USING btree (id_usuario);


--
-- Name: anotacion_calendario_id_usuario_autor_bfb6a02d; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX anotacion_calendario_id_usuario_autor_bfb6a02d ON public.anotacion_calendario USING btree (id_usuario_autor);


--
-- Name: anotacion_id_cliente_7b440f86; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX anotacion_id_cliente_7b440f86 ON public.anotacion USING btree (id_cliente);


--
-- Name: anotacion_id_usuario_d3bd44f8; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX anotacion_id_usuario_d3bd44f8 ON public.anotacion USING btree (id_usuario);


--
-- Name: campo_plantilla_id_plantilla_a0411d48; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX campo_plantilla_id_plantilla_a0411d48 ON public.campo_plantilla USING btree (id_plantilla);


--
-- Name: cliente_id_usuario_responsable_ad23c1b9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cliente_id_usuario_responsable_ad23c1b9 ON public.cliente USING btree (id_usuario_responsable);


--
-- Name: cliente_municipio_id_cliente_400413b1; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cliente_municipio_id_cliente_400413b1 ON public.cliente_municipio USING btree (id_cliente);


--
-- Name: cliente_servicio_id_cliente_ed26107a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cliente_servicio_id_cliente_ed26107a ON public.cliente_servicio USING btree (id_cliente);


--
-- Name: cliente_servicio_id_tipo_servicio_c229a531; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cliente_servicio_id_tipo_servicio_c229a531 ON public.cliente_servicio USING btree (id_tipo_servicio);


--
-- Name: comunicacion_id_cliente_c239e10b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX comunicacion_id_cliente_c239e10b ON public.comunicacion USING btree (id_cliente);


--
-- Name: comunicacion_id_usuario_57ee1015; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX comunicacion_id_usuario_57ee1015 ON public.comunicacion USING btree (id_usuario);


--
-- Name: concepto_facturable_nombre_concepto_cefc2015_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX concepto_facturable_nombre_concepto_cefc2015_like ON public.concepto_facturable USING btree (nombre_concepto varchar_pattern_ops);


--
-- Name: configuracion_alerta_id_vencimiento_b1bf85cd; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX configuracion_alerta_id_vencimiento_b1bf85cd ON public.configuracion_alerta USING btree (id_vencimiento);


--
-- Name: credencial_id_cliente_513a9eac; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX credencial_id_cliente_513a9eac ON public.credencial USING btree (id_cliente);


--
-- Name: cuenta_cobro_detalle_id_concepto_1ba35cc0; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cuenta_cobro_detalle_id_concepto_1ba35cc0 ON public.cuenta_cobro_detalle USING btree (id_concepto);


--
-- Name: cuenta_cobro_detalle_id_cuenta_cobro_27569489; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cuenta_cobro_detalle_id_cuenta_cobro_27569489 ON public.cuenta_cobro_detalle USING btree (id_cuenta_cobro);


--
-- Name: cuenta_cobro_id_cliente_24ce1dea; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cuenta_cobro_id_cliente_24ce1dea ON public.cuenta_cobro USING btree (id_cliente);


--
-- Name: cuenta_cobro_id_cuenta_bancaria_4aaef5f8; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cuenta_cobro_id_cuenta_bancaria_4aaef5f8 ON public.cuenta_cobro USING btree (id_cuenta_bancaria);


--
-- Name: cuenta_cobro_id_honorario_78fbdb88; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cuenta_cobro_id_honorario_78fbdb88 ON public.cuenta_cobro USING btree (id_honorario);


--
-- Name: cuenta_cobro_id_metodo_pago_01a5eeba; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cuenta_cobro_id_metodo_pago_01a5eeba ON public.cuenta_cobro USING btree (id_metodo_pago);


--
-- Name: documento_detalle_id_campo_ebbfd118; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX documento_detalle_id_campo_ebbfd118 ON public.documento_detalle USING btree (id_campo);


--
-- Name: documento_detalle_id_documento_d152a4f4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX documento_detalle_id_documento_d152a4f4 ON public.documento_detalle USING btree (id_documento);


--
-- Name: documento_id_cliente_e34623aa; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX documento_id_cliente_e34623aa ON public.documento USING btree (id_cliente);


--
-- Name: documento_id_plantilla_7ba0befa; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX documento_id_plantilla_7ba0befa ON public.documento USING btree (id_plantilla);


--
-- Name: documento_id_usuario_generador_e584f598; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX documento_id_usuario_generador_e584f598 ON public.documento USING btree (id_usuario_generador);


--
-- Name: documento_valor_id_campo_e1d4a0bb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX documento_valor_id_campo_e1d4a0bb ON public.documento_valor USING btree (id_campo);


--
-- Name: documento_valor_id_documento_2a8cb3b3; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX documento_valor_id_documento_2a8cb3b3 ON public.documento_valor USING btree (id_documento);


--
-- Name: hallazgo_id_cliente_28eb0f10; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX hallazgo_id_cliente_28eb0f10 ON public.hallazgo USING btree (id_cliente);


--
-- Name: hallazgo_id_usuario_responsable_de6fa8f1; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX hallazgo_id_usuario_responsable_de6fa8f1 ON public.hallazgo USING btree (id_usuario_responsable);


--
-- Name: historial_tarea_id_tarea_08e1f6b6; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX historial_tarea_id_tarea_08e1f6b6 ON public.historial_tarea USING btree (id_tarea);


--
-- Name: historial_tarea_id_usuario_f5b8bd8c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX historial_tarea_id_usuario_f5b8bd8c ON public.historial_tarea USING btree (id_usuario);


--
-- Name: honorario_id_usuario_actualizacion_d6fe930c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX honorario_id_usuario_actualizacion_d6fe930c ON public.honorario USING btree (id_usuario_actualizacion);


--
-- Name: honorario_servicio_id_honorario_b416943b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX honorario_servicio_id_honorario_b416943b ON public.honorario_servicio USING btree (id_honorario);


--
-- Name: honorario_servicio_id_tipo_servicio_801daba0; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX honorario_servicio_id_tipo_servicio_801daba0 ON public.honorario_servicio USING btree (id_tipo_servicio);


--
-- Name: configuracion_cobro_id_cuenta_bancaria_9f91ed81; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX configuracion_cobro_id_cuenta_bancaria_9f91ed81 ON public.configuracion_cobro USING btree (id_cuenta_bancaria);


--
-- Name: configuracion_cobro_id_metodo_pago_acc7871f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX configuracion_cobro_id_metodo_pago_acc7871f ON public.configuracion_cobro USING btree (id_metodo_pago);


--
-- Name: envio_programado_id_comunicacion_4a470a70; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX envio_programado_id_comunicacion_4a470a70 ON public.envio_programado USING btree (id_comunicacion);


--
-- Name: envio_programado_id_cuenta_cobro_23fb05ed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX envio_programado_id_cuenta_cobro_23fb05ed ON public.envio_programado USING btree (id_cuenta_cobro);


--
-- Name: envio_programado_id_usuario_4dfa2705; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX envio_programado_id_usuario_4dfa2705 ON public.envio_programado USING btree (id_usuario);


--
-- Name: idx_envio_estado_fecha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envio_estado_fecha ON public.envio_programado USING btree (estado, fecha_programada);


--
-- Name: idx_abono_cuenta; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_abono_cuenta ON public.abono USING btree (id_cuenta_cobro, fecha);


--
-- Name: idx_adjunto_origen; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_adjunto_origen ON public.adjunto USING btree (tabla_origen, id_origen);


--
-- Name: idx_anotacion_cliente; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_anotacion_cliente ON public.anotacion USING btree (id_cliente, fecha_hora DESC);


--
-- Name: idx_cliente_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cliente_estado ON public.cliente USING btree (estado);


--
-- Name: idx_cliente_nit; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cliente_nit ON public.cliente USING btree (nit_cedula);


--
-- Name: idx_comunicacion_cliente; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_comunicacion_cliente ON public.comunicacion USING btree (id_cliente, fecha_hora DESC);


--
-- Name: idx_cuenta_cobro_cliente; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cuenta_cobro_cliente ON public.cuenta_cobro USING btree (id_cliente, estado_pago);


--
-- Name: idx_cuenta_cobro_vencimiento; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cuenta_cobro_vencimiento ON public.cuenta_cobro USING btree (fecha_vencimiento_pago);


--
-- Name: idx_documento_cliente; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documento_cliente ON public.documento USING btree (id_cliente, id_plantilla);


--
-- Name: idx_hallazgo_cliente; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hallazgo_cliente ON public.hallazgo USING btree (id_cliente, estado);


--
-- Name: idx_hallazgo_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hallazgo_estado ON public.hallazgo USING btree (estado);


--
-- Name: idx_tarea_cliente; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tarea_cliente ON public.tarea USING btree (id_cliente, estado);


--
-- Name: idx_tarea_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tarea_estado ON public.tarea USING btree (estado);


--
-- Name: idx_vencimiento_cliente; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vencimiento_cliente ON public.vencimiento USING btree (id_cliente, fecha_vencimiento);


--
-- Name: idx_vencimiento_fecha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vencimiento_fecha ON public.vencimiento USING btree (fecha_vencimiento);


--
-- Name: metodo_pago_nombre_metodo_42d8a058_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX metodo_pago_nombre_metodo_42d8a058_like ON public.metodo_pago USING btree (nombre_metodo varchar_pattern_ops);


--
-- Name: modulo_codigo_modulo_fa34fe53_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX modulo_codigo_modulo_fa34fe53_like ON public.modulo USING btree (codigo_modulo varchar_pattern_ops);


--
-- Name: observacion_tarea_id_tarea_f7ed11b7; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX observacion_tarea_id_tarea_f7ed11b7 ON public.observacion_tarea USING btree (id_tarea);


--
-- Name: observacion_tarea_id_usuario_fca8c926; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX observacion_tarea_id_usuario_fca8c926 ON public.observacion_tarea USING btree (id_usuario);


--
-- Name: permiso_reporte_rol_id_reporte_ee00d9bf; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX permiso_reporte_rol_id_reporte_ee00d9bf ON public.permiso_reporte_rol USING btree (id_reporte);


--
-- Name: permiso_reporte_rol_id_rol_bb322076; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX permiso_reporte_rol_id_rol_bb322076 ON public.permiso_reporte_rol USING btree (id_rol);


--
-- Name: permiso_rol_modulo_id_modulo_39757aa1; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX permiso_rol_modulo_id_modulo_39757aa1 ON public.permiso_rol_modulo USING btree (id_modulo);


--
-- Name: permiso_rol_modulo_id_rol_7624a906; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX permiso_rol_modulo_id_rol_7624a906 ON public.permiso_rol_modulo USING btree (id_rol);


--
-- Name: reporte_nombre_reporte_59803755_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX reporte_nombre_reporte_59803755_like ON public.reporte USING btree (nombre_reporte varchar_pattern_ops);


--
-- Name: rol_nombre_rol_77fbfff8_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX rol_nombre_rol_77fbfff8_like ON public.rol USING btree (nombre_rol varchar_pattern_ops);


--
-- Name: tarea_id_cliente_67d1a3d7; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tarea_id_cliente_67d1a3d7 ON public.tarea USING btree (id_cliente);


--
-- Name: tarea_id_usuario_responsable_d96c02e2; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tarea_id_usuario_responsable_d96c02e2 ON public.tarea USING btree (id_usuario_responsable);


--
-- Name: tipo_servicio_nombre_servicio_13b7e681_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tipo_servicio_nombre_servicio_13b7e681_like ON public.tipo_servicio USING btree (nombre_servicio varchar_pattern_ops);


--
-- Name: usuario_correo_5d0f2e9c_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX usuario_correo_5d0f2e9c_like ON public.usuario USING btree (correo varchar_pattern_ops);


--
-- Name: usuario_id_rol_948a2916; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX usuario_id_rol_948a2916 ON public.usuario USING btree (id_rol);


--
-- Name: vencimiento_id_cliente_9e4a1874; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX vencimiento_id_cliente_9e4a1874 ON public.vencimiento USING btree (id_cliente);


--
-- Name: vencimiento_id_tarea_7f55dc35; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX vencimiento_id_tarea_7f55dc35 ON public.vencimiento USING btree (id_tarea);


--
-- Name: vencimiento_id_usuario_responsable_6bad33c0; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX vencimiento_id_usuario_responsable_6bad33c0 ON public.vencimiento USING btree (id_usuario_responsable);


--
-- Name: abono trg_abono_calcular_saldo; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_abono_calcular_saldo
    BEFORE INSERT ON public.abono
    FOR EACH ROW EXECUTE FUNCTION public.fn_abono_calcular_saldo();


--
-- Name: abono trg_abono_actualizar_estado; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_abono_actualizar_estado
    AFTER INSERT ON public.abono
    FOR EACH ROW EXECUTE FUNCTION public.fn_abono_actualizar_estado_cuenta();


--
-- Name: abono trg_abono_inmutable; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_abono_inmutable
    BEFORE UPDATE OR DELETE ON public.abono
    FOR EACH ROW EXECUTE FUNCTION public.fn_abono_inmutable();


--
-- Name: abono abono_id_cuenta_cobro_7f49f5d6_fk_cuenta_cobro_id_cuenta_cobro; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.abono
    ADD CONSTRAINT abono_id_cuenta_cobro_7f49f5d6_fk_cuenta_cobro_id_cuenta_cobro FOREIGN KEY (id_cuenta_cobro) REFERENCES public.cuenta_cobro(id_cuenta_cobro) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: abono abono_id_metodo_pago_7a0a104c_fk_metodo_pago_id_metodo_pago; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.abono
    ADD CONSTRAINT abono_id_metodo_pago_7a0a104c_fk_metodo_pago_id_metodo_pago FOREIGN KEY (id_metodo_pago) REFERENCES public.metodo_pago(id_metodo_pago) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: abono abono_id_usuario_responsable_4125996e_fk_usuario_id_usuario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.abono
    ADD CONSTRAINT abono_id_usuario_responsable_4125996e_fk_usuario_id_usuario FOREIGN KEY (id_usuario_responsable) REFERENCES public.usuario(id_usuario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: anotacion_calendario_destinatario anotacion_calendario_id_anotacion_cal_0c50ca98_fk_anotacion; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anotacion_calendario_destinatario
    ADD CONSTRAINT anotacion_calendario_id_anotacion_cal_0c50ca98_fk_anotacion FOREIGN KEY (id_anotacion_cal) REFERENCES public.anotacion_calendario(id_anotacion_cal) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: anotacion_calendario_destinatario anotacion_calendario_id_usuario_10833146_fk_usuario_i; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anotacion_calendario_destinatario
    ADD CONSTRAINT anotacion_calendario_id_usuario_10833146_fk_usuario_i FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: anotacion_calendario anotacion_calendario_id_usuario_autor_bfb6a02d_fk_usuario_i; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anotacion_calendario
    ADD CONSTRAINT anotacion_calendario_id_usuario_autor_bfb6a02d_fk_usuario_i FOREIGN KEY (id_usuario_autor) REFERENCES public.usuario(id_usuario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: anotacion anotacion_id_cliente_7b440f86_fk_cliente_id_cliente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anotacion
    ADD CONSTRAINT anotacion_id_cliente_7b440f86_fk_cliente_id_cliente FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: anotacion anotacion_id_usuario_d3bd44f8_fk_usuario_id_usuario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anotacion
    ADD CONSTRAINT anotacion_id_usuario_d3bd44f8_fk_usuario_id_usuario FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: campo_plantilla campo_plantilla_id_plantilla_a0411d48_fk_plantilla_id_plantilla; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campo_plantilla
    ADD CONSTRAINT campo_plantilla_id_plantilla_a0411d48_fk_plantilla_id_plantilla FOREIGN KEY (id_plantilla) REFERENCES public.plantilla(id_plantilla) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cliente cliente_id_usuario_responsable_ad23c1b9_fk_usuario_id_usuario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_id_usuario_responsable_ad23c1b9_fk_usuario_id_usuario FOREIGN KEY (id_usuario_responsable) REFERENCES public.usuario(id_usuario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cliente_municipio cliente_municipio_id_cliente_400413b1_fk_cliente_id_cliente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente_municipio
    ADD CONSTRAINT cliente_municipio_id_cliente_400413b1_fk_cliente_id_cliente FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cliente_servicio cliente_servicio_id_cliente_ed26107a_fk_cliente_id_cliente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente_servicio
    ADD CONSTRAINT cliente_servicio_id_cliente_ed26107a_fk_cliente_id_cliente FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cliente_servicio cliente_servicio_id_tipo_servicio_c229a531_fk_tipo_serv; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente_servicio
    ADD CONSTRAINT cliente_servicio_id_tipo_servicio_c229a531_fk_tipo_serv FOREIGN KEY (id_tipo_servicio) REFERENCES public.tipo_servicio(id_tipo_servicio) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: comunicacion comunicacion_id_cliente_c239e10b_fk_cliente_id_cliente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comunicacion
    ADD CONSTRAINT comunicacion_id_cliente_c239e10b_fk_cliente_id_cliente FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: comunicacion comunicacion_id_usuario_57ee1015_fk_usuario_id_usuario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comunicacion
    ADD CONSTRAINT comunicacion_id_usuario_57ee1015_fk_usuario_id_usuario FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: configuracion_alerta configuracion_alerta_id_vencimiento_b1bf85cd_fk_vencimien; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuracion_alerta
    ADD CONSTRAINT configuracion_alerta_id_vencimiento_b1bf85cd_fk_vencimien FOREIGN KEY (id_vencimiento) REFERENCES public.vencimiento(id_vencimiento) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: credencial credencial_id_cliente_513a9eac_fk_cliente_id_cliente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.credencial
    ADD CONSTRAINT credencial_id_cliente_513a9eac_fk_cliente_id_cliente FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cuenta_cobro_detalle cuenta_cobro_detalle_id_concepto_1ba35cc0_fk_concepto_; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuenta_cobro_detalle
    ADD CONSTRAINT cuenta_cobro_detalle_id_concepto_1ba35cc0_fk_concepto_ FOREIGN KEY (id_concepto) REFERENCES public.concepto_facturable(id_concepto) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cuenta_cobro_detalle cuenta_cobro_detalle_id_cuenta_cobro_27569489_fk_cuenta_co; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuenta_cobro_detalle
    ADD CONSTRAINT cuenta_cobro_detalle_id_cuenta_cobro_27569489_fk_cuenta_co FOREIGN KEY (id_cuenta_cobro) REFERENCES public.cuenta_cobro(id_cuenta_cobro) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cuenta_cobro cuenta_cobro_id_cliente_24ce1dea_fk_cliente_id_cliente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuenta_cobro
    ADD CONSTRAINT cuenta_cobro_id_cliente_24ce1dea_fk_cliente_id_cliente FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cuenta_cobro cuenta_cobro_id_cuenta_bancaria_4aaef5f8_fk_cuenta_ba; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuenta_cobro
    ADD CONSTRAINT cuenta_cobro_id_cuenta_bancaria_4aaef5f8_fk_cuenta_ba FOREIGN KEY (id_cuenta_bancaria) REFERENCES public.cuenta_bancaria(id_cuenta_bancaria) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cuenta_cobro cuenta_cobro_id_honorario_78fbdb88_fk_honorario_id_honorario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuenta_cobro
    ADD CONSTRAINT cuenta_cobro_id_honorario_78fbdb88_fk_honorario_id_honorario FOREIGN KEY (id_honorario) REFERENCES public.honorario(id_honorario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cuenta_cobro cuenta_cobro_id_metodo_pago_01a5eeba_fk_metodo_pa; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cuenta_cobro
    ADD CONSTRAINT cuenta_cobro_id_metodo_pago_01a5eeba_fk_metodo_pa FOREIGN KEY (id_metodo_pago) REFERENCES public.metodo_pago(id_metodo_pago) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: documento_detalle documento_detalle_id_campo_ebbfd118_fk_campo_plantilla_id_campo; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento_detalle
    ADD CONSTRAINT documento_detalle_id_campo_ebbfd118_fk_campo_plantilla_id_campo FOREIGN KEY (id_campo) REFERENCES public.campo_plantilla(id_campo) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: documento_detalle documento_detalle_id_documento_d152a4f4_fk_documento; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento_detalle
    ADD CONSTRAINT documento_detalle_id_documento_d152a4f4_fk_documento FOREIGN KEY (id_documento) REFERENCES public.documento(id_documento) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: documento documento_id_cliente_e34623aa_fk_cliente_id_cliente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento
    ADD CONSTRAINT documento_id_cliente_e34623aa_fk_cliente_id_cliente FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: documento documento_id_plantilla_7ba0befa_fk_plantilla_id_plantilla; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento
    ADD CONSTRAINT documento_id_plantilla_7ba0befa_fk_plantilla_id_plantilla FOREIGN KEY (id_plantilla) REFERENCES public.plantilla(id_plantilla) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: documento documento_id_usuario_generador_e584f598_fk_usuario_id_usuario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento
    ADD CONSTRAINT documento_id_usuario_generador_e584f598_fk_usuario_id_usuario FOREIGN KEY (id_usuario_generador) REFERENCES public.usuario(id_usuario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: documento_valor documento_valor_id_campo_e1d4a0bb_fk_campo_plantilla_id_campo; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento_valor
    ADD CONSTRAINT documento_valor_id_campo_e1d4a0bb_fk_campo_plantilla_id_campo FOREIGN KEY (id_campo) REFERENCES public.campo_plantilla(id_campo) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: documento_valor documento_valor_id_documento_2a8cb3b3_fk_documento_id_documento; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento_valor
    ADD CONSTRAINT documento_valor_id_documento_2a8cb3b3_fk_documento_id_documento FOREIGN KEY (id_documento) REFERENCES public.documento(id_documento) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: hallazgo hallazgo_id_cliente_28eb0f10_fk_cliente_id_cliente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hallazgo
    ADD CONSTRAINT hallazgo_id_cliente_28eb0f10_fk_cliente_id_cliente FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: hallazgo hallazgo_id_usuario_responsable_de6fa8f1_fk_usuario_id_usuario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hallazgo
    ADD CONSTRAINT hallazgo_id_usuario_responsable_de6fa8f1_fk_usuario_id_usuario FOREIGN KEY (id_usuario_responsable) REFERENCES public.usuario(id_usuario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: historial_tarea historial_tarea_id_tarea_08e1f6b6_fk_tarea_id_tarea; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historial_tarea
    ADD CONSTRAINT historial_tarea_id_tarea_08e1f6b6_fk_tarea_id_tarea FOREIGN KEY (id_tarea) REFERENCES public.tarea(id_tarea) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: historial_tarea historial_tarea_id_usuario_f5b8bd8c_fk_usuario_id_usuario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historial_tarea
    ADD CONSTRAINT historial_tarea_id_usuario_f5b8bd8c_fk_usuario_id_usuario FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: honorario honorario_id_cliente_50ce0708_fk_cliente_id_cliente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.honorario
    ADD CONSTRAINT honorario_id_cliente_50ce0708_fk_cliente_id_cliente FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: honorario honorario_id_usuario_actualiza_d6fe930c_fk_usuario_i; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.honorario
    ADD CONSTRAINT honorario_id_usuario_actualiza_d6fe930c_fk_usuario_i FOREIGN KEY (id_usuario_actualizacion) REFERENCES public.usuario(id_usuario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: honorario_servicio honorario_servicio_id_honorario_b416943b_fk_honorario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.honorario_servicio
    ADD CONSTRAINT honorario_servicio_id_honorario_b416943b_fk_honorario FOREIGN KEY (id_honorario) REFERENCES public.honorario(id_honorario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: honorario_servicio honorario_servicio_id_tipo_servicio_801daba0_fk_tipo_serv; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.honorario_servicio
    ADD CONSTRAINT honorario_servicio_id_tipo_servicio_801daba0_fk_tipo_serv FOREIGN KEY (id_tipo_servicio) REFERENCES public.tipo_servicio(id_tipo_servicio) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: configuracion_cobro configuracion_cobro_id_cuenta_bancaria_9f91ed81_fk_cuenta_ba; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuracion_cobro
    ADD CONSTRAINT configuracion_cobro_id_cuenta_bancaria_9f91ed81_fk_cuenta_ba FOREIGN KEY (id_cuenta_bancaria) REFERENCES public.cuenta_bancaria(id_cuenta_bancaria) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: configuracion_cobro configuracion_cobro_id_metodo_pago_acc7871f_fk_metodo_pa; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuracion_cobro
    ADD CONSTRAINT configuracion_cobro_id_metodo_pago_acc7871f_fk_metodo_pa FOREIGN KEY (id_metodo_pago) REFERENCES public.metodo_pago(id_metodo_pago) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: envio_programado envio_programado_id_comunicacion_4a470a70_fk_comunicac; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envio_programado
    ADD CONSTRAINT envio_programado_id_comunicacion_4a470a70_fk_comunicac FOREIGN KEY (id_comunicacion) REFERENCES public.comunicacion(id_comunicacion) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: envio_programado envio_programado_id_cuenta_cobro_23fb05ed_fk_cuenta_co; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envio_programado
    ADD CONSTRAINT envio_programado_id_cuenta_cobro_23fb05ed_fk_cuenta_co FOREIGN KEY (id_cuenta_cobro) REFERENCES public.cuenta_cobro(id_cuenta_cobro) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: envio_programado envio_programado_id_usuario_4dfa2705_fk_usuario_id_usuario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envio_programado
    ADD CONSTRAINT envio_programado_id_usuario_4dfa2705_fk_usuario_id_usuario FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: observacion_tarea observacion_tarea_id_tarea_f7ed11b7_fk_tarea_id_tarea; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.observacion_tarea
    ADD CONSTRAINT observacion_tarea_id_tarea_f7ed11b7_fk_tarea_id_tarea FOREIGN KEY (id_tarea) REFERENCES public.tarea(id_tarea) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: observacion_tarea observacion_tarea_id_usuario_fca8c926_fk_usuario_id_usuario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.observacion_tarea
    ADD CONSTRAINT observacion_tarea_id_usuario_fca8c926_fk_usuario_id_usuario FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: permiso_reporte_rol permiso_reporte_rol_id_reporte_ee00d9bf_fk_reporte_id_reporte; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permiso_reporte_rol
    ADD CONSTRAINT permiso_reporte_rol_id_reporte_ee00d9bf_fk_reporte_id_reporte FOREIGN KEY (id_reporte) REFERENCES public.reporte(id_reporte) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: permiso_reporte_rol permiso_reporte_rol_id_rol_bb322076_fk_rol_id_rol; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permiso_reporte_rol
    ADD CONSTRAINT permiso_reporte_rol_id_rol_bb322076_fk_rol_id_rol FOREIGN KEY (id_rol) REFERENCES public.rol(id_rol) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: permiso_rol_modulo permiso_rol_modulo_id_modulo_39757aa1_fk_modulo_id_modulo; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permiso_rol_modulo
    ADD CONSTRAINT permiso_rol_modulo_id_modulo_39757aa1_fk_modulo_id_modulo FOREIGN KEY (id_modulo) REFERENCES public.modulo(id_modulo) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: permiso_rol_modulo permiso_rol_modulo_id_rol_7624a906_fk_rol_id_rol; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permiso_rol_modulo
    ADD CONSTRAINT permiso_rol_modulo_id_rol_7624a906_fk_rol_id_rol FOREIGN KEY (id_rol) REFERENCES public.rol(id_rol) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: tarea tarea_id_cliente_67d1a3d7_fk_cliente_id_cliente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tarea
    ADD CONSTRAINT tarea_id_cliente_67d1a3d7_fk_cliente_id_cliente FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: tarea tarea_id_usuario_responsable_d96c02e2_fk_usuario_id_usuario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tarea
    ADD CONSTRAINT tarea_id_usuario_responsable_d96c02e2_fk_usuario_id_usuario FOREIGN KEY (id_usuario_responsable) REFERENCES public.usuario(id_usuario) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: usuario usuario_id_rol_948a2916_fk_rol_id_rol; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_id_rol_948a2916_fk_rol_id_rol FOREIGN KEY (id_rol) REFERENCES public.rol(id_rol) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: vencimiento vencimiento_id_cliente_9e4a1874_fk_cliente_id_cliente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vencimiento
    ADD CONSTRAINT vencimiento_id_cliente_9e4a1874_fk_cliente_id_cliente FOREIGN KEY (id_cliente) REFERENCES public.cliente(id_cliente) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: vencimiento vencimiento_id_tarea_7f55dc35_fk_tarea_id_tarea; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vencimiento
    ADD CONSTRAINT vencimiento_id_tarea_7f55dc35_fk_tarea_id_tarea FOREIGN KEY (id_tarea) REFERENCES public.tarea(id_tarea) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: vencimiento vencimiento_id_usuario_responsab_6bad33c0_fk_usuario_i; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vencimiento
    ADD CONSTRAINT vencimiento_id_usuario_responsab_6bad33c0_fk_usuario_i FOREIGN KEY (id_usuario_responsable) REFERENCES public.usuario(id_usuario) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--

\unrestrict vzljRXeDMnxgnYVzuunOG3e1a6aJXUxxLyENtAadYdWC2rZrrmUVasdwfysw6gw

