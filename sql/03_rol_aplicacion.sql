-- =====================================================================
-- Rol de mínimo privilegio para la API (hallazgo H-13, REQ-NF-05)
--
-- La API NO debe conectarse como dueño de la base ni como superusuario:
--   * `salesx_app`  → solo lee y escribe datos (lo usa la API en ejecución).
--   * dueño (p. ej. `salesx`) → crea el esquema y aplica migraciones (sql/01, sql/04).
-- La bitácora `auditoria_pedido` queda de SOLO-AGREGAR: el rol de la API puede
-- leer e insertar, pero no modificar ni borrar eventos.
--
-- Ejecutar como superusuario, conectado A LA BASE de la aplicación:
--   psql -U postgres -h localhost -d salesx -v app_password=<clave> -f sql/03_rol_aplicacion.sql
-- Opcional: -v owner=<dueño de las tablas>   (por defecto: salesx)
-- Es idempotente: se puede repetir (también sirve para rotar la contraseña).
-- Vuelva a ejecutarlo después de CREAR tablas nuevas (migraciones) para darles acceso a la API.
-- =====================================================================
\if :{?app_password}
\else
  \echo 'ERROR: defina la contrasena del rol con  -v app_password=<clave>'
  \quit
\endif
\if :{?owner}
\else
  \set owner salesx
\endif
\set ON_ERROR_STOP on

-- 1) Rol (se crea si no existe) y contraseña
SELECT 'CREATE ROLE salesx_app LOGIN'
 WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'salesx_app') \gexec
ALTER ROLE salesx_app WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'app_password';

-- 2) Acceso a la base y al esquema (sin permiso para crear objetos)
SELECT format('GRANT CONNECT ON DATABASE %I TO salesx_app', current_database()) \gexec
GRANT USAGE ON SCHEMA public TO salesx_app;
REVOKE CREATE ON SCHEMA public FROM salesx_app;

-- 3) Datos: lectura y escritura en las tablas existentes
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO salesx_app;

-- 4) SIN privilegios por defecto sobre tablas futuras (falla cerrada).
--    Una tabla creada o recreada por el dueño NO queda accesible para la API hasta volver a ejecutar
--    este script. Así, restaurar un respaldo con `pg_restore --clean` reproduce exactamente los
--    permisos del respaldo y la auditoría sigue siendo de solo-agregar. (Una versión anterior daba
--    permisos por defecto y, tras restaurar, devolvía UPDATE/DELETE sobre la auditoría.)
--    Este REVOKE también limpia los permisos por defecto que dejara esa versión anterior.
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner" IN SCHEMA public
  REVOKE ALL ON TABLES FROM salesx_app;

-- 5) Auditoría de solo-agregar
REVOKE UPDATE, DELETE, TRUNCATE ON auditoria_pedido FROM salesx_app;

-- 6) Comprobación (debe mostrar: ver=t, insertar=t, actualizar=f, borrar=f)
SELECT has_table_privilege('salesx_app', 'auditoria_pedido', 'SELECT')  AS ver,
       has_table_privilege('salesx_app', 'auditoria_pedido', 'INSERT')  AS insertar,
       has_table_privilege('salesx_app', 'auditoria_pedido', 'UPDATE')  AS actualizar,
       has_table_privilege('salesx_app', 'auditoria_pedido', 'DELETE')  AS borrar;
