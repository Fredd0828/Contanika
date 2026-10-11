-- ============================================================
-- Contanika - Roles de base de datos con privilegios mínimos (pr01, control 3)
--
-- La aplicación NO se conecta con el superusuario `postgres`. Se usan dos
-- roles propios:
--
--   contanika_dueno  Dueño de las tablas. Solo se usa para aplicar
--                    migraciones (`python gestionar.py migrate`).
--   contanika_app    El que usa el sistema en marcha. Solo lee y escribe
--                    filas: no crea, altera ni borra tablas.
--
-- Cómo ejecutarlo (una sola vez, en producción):
--   1. Reemplace las dos contraseñas de abajo por unas largas y aleatorias.
--   2. Ejecútelo como `postgres` (en Supabase: SQL Editor) ANTES de migrar.
--   3. Aplique las migraciones con BD_USUARIO=contanika_dueno.
--   4. Vuelva a ejecutar la sección «Privilegios» de este script (las tablas
--      ya existen) y luego `04_activar_rls.sql`.
--   5. Deje en el .env del servidor BD_USUARIO=contanika_app.
--
-- Es idempotente: se puede volver a ejecutar sin daño. No guarde este
-- archivo con las contraseñas reales.
-- ============================================================

-- ------------------------------------------------------------
-- Roles
-- ------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'contanika_dueno') THEN
        CREATE ROLE contanika_dueno LOGIN PASSWORD 'CAMBIE_ESTA_CLAVE_DEL_DUENO'
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'contanika_app') THEN
        CREATE ROLE contanika_app LOGIN PASSWORD 'CAMBIE_ESTA_CLAVE_DE_LA_APLICACION'
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
    END IF;
END
$$;

-- En Supabase `postgres` no es superusuario: para dar privilegios sobre las
-- tablas del dueño y activarles RLS (script 04) debe ser miembro de ese rol.
GRANT contanika_dueno TO CURRENT_USER;

-- El dueño crea las tablas en el esquema público; la aplicación solo lo usa.
GRANT USAGE, CREATE ON SCHEMA public TO contanika_dueno;
GRANT USAGE ON SCHEMA public TO contanika_app;

-- ------------------------------------------------------------
-- Privilegios (repetir después de la primera migración)
-- ------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO contanika_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO contanika_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO contanika_app;

-- Las tablas que el dueño cree en adelante heredan los mismos privilegios.
ALTER DEFAULT PRIVILEGES FOR ROLE contanika_dueno IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO contanika_app;
ALTER DEFAULT PRIVILEGES FOR ROLE contanika_dueno IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO contanika_app;
ALTER DEFAULT PRIVILEGES FOR ROLE contanika_dueno IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO contanika_app;

-- Nadie más entra al esquema por el permiso general de PostgreSQL.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
