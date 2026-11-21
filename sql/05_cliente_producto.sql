-- SALES-X v1.3 · tablas locales CLIENTE y PRODUCTO + llaves foráneas.
-- Ejecutar como dueño (salesx):  psql -U salesx -d salesx -f sql/05_cliente_producto.sql
-- Requisito: haber iniciado la API una vez (sincroniza el catálogo) o cargar los datos antes de las FK.
BEGIN;

CREATE TABLE IF NOT EXISTS cliente (
    cliente_id           UUID         PRIMARY KEY,
    nombre               VARCHAR(160) NOT NULL,
    documento            VARCHAR(40),
    correo               VARCHAR(160),
    fecha_sincronizacion TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_cliente_documento ON cliente (documento);

CREATE TABLE IF NOT EXISTS producto (
    producto_id          UUID           PRIMARY KEY,
    nombre               VARCHAR(160)   NOT NULL,
    sku                  VARCHAR(40),
    precio               NUMERIC(14, 2) NOT NULL,
    disponible           INTEGER        NOT NULL DEFAULT 0,
    activo               BOOLEAN        NOT NULL DEFAULT TRUE,
    fecha_sincronizacion TIMESTAMPTZ    NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_producto_sku ON producto (sku);
CREATE INDEX IF NOT EXISTS ix_detalle_producto ON detalle_pedido (producto_id);

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pedido_cliente_id_fkey') THEN
    ALTER TABLE pedido ADD CONSTRAINT pedido_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES cliente (cliente_id);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'detalle_pedido_producto_id_fkey') THEN
    ALTER TABLE detalle_pedido ADD CONSTRAINT detalle_pedido_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES producto (producto_id);
  END IF;
END $$;

COMMIT;
