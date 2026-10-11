-- ============================================================
-- Contanika - Seguridad a nivel de fila, RLS (pr01, control 4)
--
-- Por qué: Supabase publica cada tabla del esquema `public` por su API
-- (PostgREST) usando la clave pública «anon». Sin RLS, cualquiera con esa
-- clave podría leer o escribir las tablas sin pasar por Contanika.
--
-- Qué hace, en todas las tablas del esquema `public`:
--   1. Activa RLS: lo que no tenga una política queda negado.
--   2. Crea una única política que deja pasar SOLO a los roles de la
--      aplicación (`contanika_app` y `contanika_dueno`). Quién ve qué
--      dentro del sistema lo sigue decidiendo Contanika (roles y módulos).
--   3. Les quita todos los privilegios a los roles públicos de Supabase
--      (`anon` y `authenticated`), si existen.
--
-- Cómo ejecutarlo: como `postgres` (en Supabase: SQL Editor), después de
-- `03_rol_aplicacion.sql` y de aplicar las migraciones. Vuelva a ejecutarlo
-- cada vez que una migración cree tablas nuevas. Es idempotente.
--
-- Verificación: la última consulta lista las tablas que quedaran sin RLS;
-- debe devolver cero filas.
-- ============================================================

DO $$
DECLARE
    tabla record;
    roles_aplicacion text;
    rol_publico text;
BEGIN
    SELECT string_agg(quote_ident(rolname), ', ')
      INTO roles_aplicacion
      FROM pg_roles
     WHERE rolname IN ('contanika_app', 'contanika_dueno');

    IF roles_aplicacion IS NULL THEN
        RAISE EXCEPTION 'No existen los roles de la aplicación: ejecute primero 03_rol_aplicacion.sql';
    END IF;

    FOR tabla IN
        SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY', tabla.schemaname, tabla.tablename);
        EXECUTE format('DROP POLICY IF EXISTS acceso_aplicacion ON %I.%I', tabla.schemaname, tabla.tablename);
        EXECUTE format(
            'CREATE POLICY acceso_aplicacion ON %I.%I FOR ALL TO %s USING (true) WITH CHECK (true)',
            tabla.schemaname, tabla.tablename, roles_aplicacion
        );
    END LOOP;

    -- Roles públicos de la API de Supabase: sin ningún privilegio sobre los datos.
    FOREACH rol_publico IN ARRAY ARRAY['anon', 'authenticated']
    LOOP
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = rol_publico) THEN
            EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA public FROM %I', rol_publico);
            EXECUTE format('REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM %I', rol_publico);
            EXECUTE format('REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM %I', rol_publico);
            EXECUTE format(
                'ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM %I', rol_publico
            );
        END IF;
    END LOOP;
END
$$;

-- Verificación: tablas del esquema público que quedaron SIN RLS (debe dar cero filas).
SELECT tablename AS tabla_sin_rls
  FROM pg_tables
 WHERE schemaname = 'public' AND NOT rowsecurity
 ORDER BY tablename;
