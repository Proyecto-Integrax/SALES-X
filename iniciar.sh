#!/usr/bin/env bash
# =====================================================================
#  SALES-X - Inicio rapido en modo local (SQLite) para Linux/macOS.
#  No requiere PostgreSQL ni Docker. Requisito: Python 3.12 o superior.
#  Uso:  bash iniciar.sh
# =====================================================================
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "No se encontro python3. Instale Python 3.12 o superior (Debian/Ubuntu: sudo apt install python3 python3-venv python3-pip)."
  exit 1
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'; then
  echo "Se necesita Python 3.12 o superior. Version encontrada: $(python3 --version)"
  exit 1
fi

[ -f .env ] || cp .env.example .env

if [ ! -d .venv ]; then
  python3 -m venv .venv || { echo "No se pudo crear el entorno virtual (Debian/Ubuntu: sudo apt install python3-venv)."; exit 1; }
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "Instalando dependencias (la primera vez tarda un poco)..."
python -m pip install -q -r requirements.txt || { echo "No se pudieron instalar las dependencias. Revise su conexion a Internet."; exit 1; }

if [ ! -f sales_x.db ]; then
  echo "Creando la base de datos con 40 pedidos de demostracion..."
  python -m app.demo
fi

echo
echo "==================================================================="
echo "  SALES-X en  http://localhost:8000      (documentacion de la API: /docs)"
echo
echo "  Administrador:  admin@salesx.local     contrasena: Admin2026*"
echo "  Vendedor:       vendedor@salesx.local  contrasena: Ventas2026*"
echo
echo "  Para detenerlo: pulse Ctrl+C."
echo "==================================================================="
echo

(command -v xdg-open >/dev/null 2>&1 && (sleep 2; xdg-open http://localhost:8000 >/dev/null 2>&1) &) || true
exec python -m uvicorn app.main:app --host localhost --port 8000
