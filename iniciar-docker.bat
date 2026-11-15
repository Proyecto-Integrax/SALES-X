@echo off
setlocal
REM =====================================================================
REM  SALES-X con Docker (modo produccion: API + PostgreSQL en contenedores).
REM  Requisito: Docker Desktop instalado y ABIERTO (motor en ejecucion).
REM =====================================================================
cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
  echo No se encontro Docker. Instale Docker Desktop: https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)
docker info >nul 2>nul
if errorlevel 1 (
  echo Docker esta instalado pero no esta en ejecucion. Abra Docker Desktop, espere a que diga "Engine running" y repita.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\generar_env_docker.ps1

echo Construyendo y levantando los contenedores ^(la primera vez descarga imagenes y tarda unos minutos^)...
docker compose --env-file .env.docker up -d --build
if errorlevel 1 (
  echo Docker Compose fallo. Revise los mensajes de arriba.
  pause
  exit /b 1
)

echo Esperando a que el sistema este listo...
set /a intentos=0
:espera
set /a intentos+=1
powershell -NoProfile -Command "try { if ((Invoke-WebRequest http://localhost:8000/health -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if not errorlevel 1 goto listo
if %intentos% GEQ 40 (
  echo El sistema no respondio a tiempo. Revise:  docker compose --env-file .env.docker logs
  pause
  exit /b 1
)
ping -n 4 127.0.0.1 >nul
goto espera

:listo
echo.
echo ===================================================================
echo   SALES-X en  http://localhost:8000
echo.
echo   Usuario:     admin@salesx.local
echo   Contrasena:  abra el archivo .env.docker y copie el valor de ADMIN_PASSWORD
echo.
echo   Este modo arranca SIN datos de demostracion (base vacia).
echo   Detener:           docker compose --env-file .env.docker down
echo   Detener y borrar:  docker compose --env-file .env.docker down -v
echo ===================================================================
start "" http://localhost:8000
pause
