-- =====================================================================
-- SALES-X - Gestión de Ventas y Pedidos  |  Esquema PostgreSQL 14+
-- Equivalente al modelo ORM (app/models.py) y al MER (docs/E1).
-- Ejecutar:  psql -U salesx -d salesx -f sql/01_schema.sql
-- (La aplicación también crea estas tablas al iniciar si no existen.)
-- =====================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS estado_pedido (
    estado_id   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre      VARCHAR(40)  NOT NULL UNIQUE,
    descripcion VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS vendedor (
    vendedor_id UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre      VARCHAR(120) NOT NULL,
    correo      VARCHAR(160) NOT NULL UNIQUE,
    contrasena  VARCHAR(100) NOT NULL,                 -- hash bcrypt, nunca texto plano
    rol         VARCHAR(20)  NOT NULL DEFAULT 'vendedor',
    activo      BOOLEAN      NOT NULL DEFAULT TRUE,
    debe_cambiar_contrasena BOOLEAN NOT NULL DEFAULT FALSE,   -- v1.1: cambio obligatorio en el siguiente ingreso
    CONSTRAINT ck_vendedor_rol CHECK (rol IN ('admin', 'vendedor'))
);

CREATE TABLE IF NOT EXISTS pedido (
    pedido_id      UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id     UUID           NOT NULL,              -- identificador común INTEGRAX (sin FK: otro microproyecto)
    estado_id      UUID           NOT NULL REFERENCES estado_pedido (estado_id),
    vendedor_id    UUID           NOT NULL REFERENCES vendedor (vendedor_id),
    subtotal       NUMERIC(14, 2) NOT NULL DEFAULT 0,
    impuestos      NUMERIC(14, 2) NOT NULL DEFAULT 0,
    descripcion    VARCHAR(500),
    total          NUMERIC(14, 2) NOT NULL DEFAULT 0,
    fecha_creacion TIMESTAMPTZ    NOT NULL DEFAULT now(),
    CONSTRAINT ck_pedido_total CHECK (total >= 0)
);
CREATE INDEX IF NOT EXISTS ix_pedido_cliente ON pedido (cliente_id);
CREATE INDEX IF NOT EXISTS ix_pedido_fecha   ON pedido (fecha_creacion);
CREATE INDEX IF NOT EXISTS ix_pedido_estado  ON pedido (estado_id);

CREATE TABLE IF NOT EXISTS detalle_pedido (
    detalle_pedido_id UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    pedido_id         UUID           NOT NULL REFERENCES pedido (pedido_id) ON DELETE CASCADE,
    producto_id       UUID           NOT NULL,           -- identificador común INTEGRAX (sin FK)
    cantidad          INTEGER        NOT NULL,
    precio_unitario   NUMERIC(14, 2) NOT NULL,
    subtotal          NUMERIC(14, 2) NOT NULL,
    CONSTRAINT ck_detalle_cantidad CHECK (cantidad > 0),
    CONSTRAINT ck_detalle_precio   CHECK (precio_unitario >= 0)
);
CREATE INDEX IF NOT EXISTS ix_detalle_pedido ON detalle_pedido (pedido_id);

CREATE TABLE IF NOT EXISTS auditoria_pedido (
    auditoria_id UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    pedido_id    UUID        NOT NULL REFERENCES pedido (pedido_id) ON DELETE CASCADE,
    vendedor_id  UUID        REFERENCES vendedor (vendedor_id),   -- NULL = acción de sistema externo
    fecha        TIMESTAMPTZ NOT NULL DEFAULT now(),
    descripcion  TEXT,
    accion       VARCHAR(40) NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_auditoria_pedido ON auditoria_pedido (pedido_id);

-- v1.1 · Fallos de inicio de sesión (bloqueo compartido entre instancias)
CREATE TABLE IF NOT EXISTS intento_login (
    intento_id UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    clave      VARCHAR(170) NOT NULL,
    fecha      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_intento_login_clave ON intento_login (clave);
CREATE INDEX IF NOT EXISTS ix_intento_login_fecha ON intento_login (fecha);

-- v1.1 · Consumidores de integración (una clave por sistema; se guarda solo el hash SHA-256)
CREATE TABLE IF NOT EXISTS consumidor_api (
    consumidor_id UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre        VARCHAR(80) NOT NULL UNIQUE,
    clave_hash    VARCHAR(64) NOT NULL UNIQUE,
    activo        BOOLEAN     NOT NULL DEFAULT TRUE,
    expira        TIMESTAMPTZ,
    creado        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ultimo_uso    TIMESTAMPTZ
);

COMMIT;
