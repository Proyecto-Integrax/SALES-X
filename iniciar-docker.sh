#!/usr/bin/env bash
# =====================================================================
#  SALES-X con Docker en Linux (modo produccion: API + PostgreSQL en contenedores).
#  Requisito: Docker con el plugin "docker compose" y el servicio en ejecucion.
#  Uso:  bash iniciar-docker.sh      (si Docker pide permisos: sudo bash iniciar-docker.sh)
# =====================================================================
set -e
cd "$(dirname "$0")"

command -v docker >/dev/null 2>&1 || { echo "No se encontro Docker. Instalelo desde https://docs.docker.com/engine/install/"; exit 1; }
docker info >/dev/null 2>&1 || { echo "Docker no responde. Inicie el servicio (sudo systemctl start docker) o use sudo."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Falta el plugin 'docker compose' (Debian/Ubuntu: sudo apt install docker-compose-v2 o docker-compose-plugin)."; exit 1; }

aleatorio() { LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c "$1"; }

if [ -f .env.docker ]; then
  echo ".env.docker ya existe: se conserva."
else
  umask 077
  cat > .env.docker <<EOF
# Configuracion para docker compose (generada automaticamente; NO subir a Git ni compartir).
POSTGRES_PASSWORD=$(aleatorio 28)
APP_DB_PASSWORD=$(aleatorio 28)
SECRET_KEY=$(aleatorio 64)
INTEGRATION_API_KEY=$(aleatorio 32)
ADMIN_EMAIL=admin@salesx.local
ADMIN_PASSWORD=$(aleatorio 16)a9
EOF
  echo ".env.docker creado con secretos aleatorios."
fi

echo "Construyendo y levantando los contenedores (la primera vez descarga imagenes y tarda unos minutos)..."
docker compose --env-file .env.docker up -d --build

echo "Esperando a que el sistema este listo..."
for i in $(seq 1 40); do
  if command -v curl >/dev/null 2>&1 && curl -fsS http://localhost:8000/health >/dev/null 2>&1; then listo=1; break; fi
  if ! command -v curl >/dev/null 2>&1 && python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=3).status==200 else 1)" 2>/dev/null; then listo=1; break; fi
  sleep 3
done
[ "${listo:-0}" = 1 ] || { echo "El sistema no respondio a tiempo. Revise:  docker compose --env-file .env.docker logs"; exit 1; }

ADMIN_PASSWORD=$(grep '^ADMIN_PASSWORD=' .env.docker | cut -d= -f2-)
echo
echo "==================================================================="
echo "  SALES-X en  http://localhost:8000"
echo
echo "  Usuario:     admin@salesx.local"
echo "  Contrasena:  $ADMIN_PASSWORD"
echo
echo "  Este modo arranca SIN datos de demostracion (base vacia)."
echo "  Detener:           docker compose --env-file .env.docker down"
echo "  Detener y borrar:  docker compose --env-file .env.docker down -v"
echo "==================================================================="
command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:8000 >/dev/null 2>&1 || true
