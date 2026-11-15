-- =====================================================================
-- Migración v1.0 -> v1.1 (idempotente: se puede ejecutar más de una vez)
-- Solo para bases creadas con la v1.0. Las bases nuevas ya la incluyen en 01_schema.sql.
--   * Cambio obligatorio de contraseña (REQ-17)
--   * Bloqueo de login compartido en BD (REQ-14)
--   * Claves de integración por consumidor (REQ-15)
-- Ejecutar:  psql -U salesx -d salesx -f sql/04_migracion_v1_1.sql
-- Después de migrar, reinicie la API: crea el consumidor «INTEGRAX-inicial» con INTEGRATION_API_KEY.
-- =====================================================================

BEGIN;

ALTER TABLE vendedor ADD COLUMN IF NOT EXISTS debe_cambiar_contrasena BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS intento_login (
    intento_id UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    clave      VARCHAR(170) NOT NULL,
    fecha      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_intento_login_clave ON intento_login (clave);
CREATE INDEX IF NOT EXISTS ix_intento_login_fecha ON intento_login (fecha);

CREATE TABLE IF NOT EXISTS consumidor_api (
    consumidor_id UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre        VARCHAR(80) NOT NULL UNIQUE,
    clave_hash    VARCHAR(64) NOT NULL UNIQUE,
    activo        BOOLEAN     NOT NULL DEFAULT TRUE,
    expira        TIMESTAMPTZ,
    creado        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ultimo_uso    TIMESTAMPTZ
);

-- Si ya existe el rol de la API (sql/03), darle acceso a las tablas nuevas.
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'salesx_app') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON intento_login, consumidor_api TO salesx_app;
  END IF;
END $$;

COMMIT;
