@echo off
setlocal
REM =====================================================================
REM  SALES-X - Inicio rapido en modo local (SQLite): no requiere PostgreSQL ni Docker.
REM  Requisito: Python 3.12 o superior (comando "py").
REM =====================================================================
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo No se encontro Python ^(comando "py"^). Instale Python 3.12 o superior desde https://www.python.org/downloads/
  echo y marque la opcion "Add python.exe to PATH" durante la instalacion.
  pause
  exit /b 1
)

if not exist .env copy .env.example .env >nul

echo Instalando dependencias ^(la primera vez tarda un poco^)...
py -m pip install -q -r requirements.txt
if errorlevel 1 (
  echo No se pudieron instalar las dependencias. Revise su conexion a Internet.
  pause
  exit /b 1
)

if not exist sales_x.db (
  echo Creando la base de datos con 40 pedidos de demostracion...
  py -m app.demo
)

echo.
echo ===================================================================
echo   SALES-X en  http://localhost:8000      ^(documentacion de la API: /docs^)
echo.
echo   Administrador:  admin@salesx.local     contrasena: Admin2026*
echo   Vendedor:       vendedor@salesx.local  contrasena: Ventas2026*
echo.
echo   Para detenerlo: cierre esta ventana o pulse Ctrl+C.
echo ===================================================================
echo.
start "" http://localhost:8000
REM --host localhost: escucha solo en este equipo (no en la red), por IPv4 e IPv6.
py -m uvicorn app.main:app --host localhost --port 8000
