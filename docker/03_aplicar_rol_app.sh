#!/bin/sh
# Crea el rol de mínimo privilegio `salesx_app` (ver sql/03_rol_aplicacion.sql).
# PostgreSQL ejecuta este archivo UNA sola vez, al crear la base por primera vez,
# después de 01_schema.sql y 02_seed_estados.sql (orden alfabético).
set -e
: "${APP_DB_PASSWORD:?Defina APP_DB_PASSWORD en el archivo .env}"

psql -v ON_ERROR_STOP=1 \
     -v app_password="$APP_DB_PASSWORD" \
     -v owner="$POSTGRES_USER" \
     --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -f /sql/03_rol_aplicacion.sql
