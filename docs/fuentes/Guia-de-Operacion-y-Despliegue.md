# Guía de Operación y Despliegue — SALES-X

Dirigida a quien instala y mantiene el sistema. Versión 1.2.0 · 14 de noviembre de 2026.

## 1. Arquitectura

```
Navegador ──HTTPS──▶ [Proxy inverso TLS] ──HTTP──▶ [API SALES-X (FastAPI/Uvicorn)] ──▶ [PostgreSQL]
Sistemas INTEGRAX ──X-API-Key (una por sistema)──▶ /api/v1/integracion/*  │
                                                                     └─REST─▶ Clientes · Productos
```

Capas del código: `routers` (HTTP) → `services` (reglas de negocio) → `models` (ORM) · `integration` (catálogo) · `static` (interfaz web).

## 2. Modo local (desarrollo / demostración) — sin instalar PostgreSQL

Requisitos: Python 3.12 o superior.

```bash
cd sales-x
python -m pip install -r requirements.txt
python -m app.demo                          # crea la BD SQLite con 40 pedidos de demostración
python -m uvicorn app.main:app --port 8000
```
En Windows basta con ejecutar `iniciar.bat` (modo local) o `iniciar-docker.bat` (Docker en modo producción; genera `.env.docker` con secretos aleatorios mediante `scripts/generar_env_docker.ps1`). Abra `http://localhost:8000`.

> **SQLite es solo para demostración:** no tiene bloqueo de fila, por lo que la protección frente a cambios de estado simultáneos (H-14) solo existe en PostgreSQL.

| Usuario | Correo | Contraseña de demostración |
|---|---|---|
| Administrador | `admin@salesx.local` | `Admin2026*` |
| Vendedor | `vendedor@salesx.local` | `Ventas2026*` |

*(Solo para pruebas locales. Ver Acta de primer ingreso.)*

### 2.0 Actualizar una base creada con la v1.0
Si ya tiene una base de la versión 1.0, aplique la migración (conserva los datos y se puede repetir) y reinicie la API:
```bash
psql -U salesx -d salesx -f sql/04_migracion_v1_1.sql
```
Agrega `vendedor.debe_cambiar_contrasena` y las tablas `intento_login` y `consumidor_api`. Al reiniciar, la API crea el consumidor «INTEGRAX-inicial» con el valor de `INTEGRATION_API_KEY`. En SQLite (desarrollo) basta con recrear la base (`python -m app.demo` tras borrar `sales_x.db`).

### 2.1 Modo local con PostgreSQL instalado (sin Docker)
1. Cree el usuario y las bases (como administrador de PostgreSQL; cambie la contraseña):
   ```sql
   CREATE ROLE salesx LOGIN PASSWORD '<contraseña>';
   CREATE DATABASE salesx OWNER salesx ENCODING 'UTF8';
   CREATE DATABASE salesx_test OWNER salesx ENCODING 'UTF8';   -- solo para pruebas
   ```
2. En `.env`: `DATABASE_URL=postgresql+psycopg2://salesx:<contraseña>@localhost:5432/salesx`
3. Inicie con `python -m app.demo` y `python -m uvicorn app.main:app --port 8000` (las tablas se crean solas; también puede aplicar `sql/01_schema.sql` y `sql/02_seed_estados.sql`).
4. Pruebas sobre PostgreSQL: defina `TEST_DATABASE_URL=postgresql+psycopg2://salesx:<contraseña>@localhost:5432/salesx_test` y ejecute `python -m pytest` (63 pruebas; con SQLite se ejecutan 60 y las 3 de concurrencia se omiten). Las pruebas **solo limpian bases cuyo nombre termina en `_test`**.

### 2.2 Rol de mínimo privilegio para la API (recomendado también en local)
La API no debe conectarse como dueño de la base. El script `sql/03_rol_aplicacion.sql` crea el rol `salesx_app`: lee y escribe datos, **no puede crear ni alterar tablas** y en `auditoria_pedido` solo puede **leer e insertar** (la auditoría queda inmutable a nivel de base de datos).
```bash
# Como superusuario de PostgreSQL, conectado a la base de la aplicación
psql -U postgres -h localhost -d salesx -v app_password=<clave> -f sql/03_rol_aplicacion.sql
```
Luego, en `.env`: `DATABASE_URL=postgresql+psycopg2://salesx_app:<clave>@localhost:5432/salesx`.

| Quién | Para qué |
|---|---|
| `salesx_app` | Lo usa la API en ejecución (y `iniciar.bat`/`app.demo` si las tablas ya existen). |
| `salesx` (dueño) | Crear el esquema (`sql/01`), migrar (`sql/04`), reiniciar datos de demostración y correr las pruebas (`TEST_DATABASE_URL`). |

El script **no concede permisos por defecto sobre tablas futuras** (falla cerrada). Consecuencias:
- **Tablas nuevas** (migraciones): la API no podrá usarlas hasta volver a ejecutar el script, o hasta incluir un `GRANT` en la migración (como hace `sql/04`).
- **Restaurar un respaldo** con `pg_restore --clean`: los permisos se restauran tal como estaban en el respaldo y la auditoría sigue siendo de solo-agregar (comprobado en Docker).
- **Si su base usó una versión anterior de este script** (que daba permisos por defecto), vuelva a ejecutarlo: elimina esos permisos. Antes de eso, una restauración con `--clean` devolvía `UPDATE`/`DELETE` sobre la auditoría.

Las migraciones se aplican con el dueño, nunca con la API.

## 3. Despliegue con Docker + PostgreSQL

1. Cree el archivo `.env` junto a `docker-compose.yml` (o un archivo aparte, p. ej. `.env.docker`, y use `docker compose --env-file .env.docker …` para no mezclarlo con el `.env` de desarrollo local):
   ```ini
   POSTGRES_PASSWORD=<contraseña larga aleatoria>
   APP_DB_PASSWORD=<contraseña del rol de la API; solo letras y números>
   SECRET_KEY=<python -c "import secrets;print(secrets.token_urlsafe(48))">
   INTEGRATION_API_KEY=<python -c "import secrets;print(secrets.token_urlsafe(32))">
   ADMIN_EMAIL=admin@su-empresa.com
   ADMIN_PASSWORD=<contraseña de al menos 10 caracteres>
   ```
2. `docker compose up -d --build`
3. Verifique: `curl http://localhost:8000/health` → `{"status":"ok","database":"ok",…}`.
4. Publique detrás de un **proxy inverso con TLS** (Nginx/Traefik); no exponga el puerto 8000 a Internet.
5. **Mínimo privilegio:** con `docker-compose` el rol `salesx_app` se crea automáticamente al inicializar la base (`docker/03_aplicar_rol_app.sh`) y la API ya lo usa. Verifique: `docker compose exec db psql -U salesx_app -d salesx -c "UPDATE auditoria_pedido SET accion = accion;"` debe responder *permission denied*. (Instalaciones sin Docker: ver §2.2.)

> **Estado de verificación (14/11/2026):** los scripts SQL, la migración y la API se verificaron sobre **PostgreSQL 18.6** (63/63 pruebas, incluidas las 3 de concurrencia), y **`docker compose` se ejecutó desde cero en modo producción** (Docker Desktop 4.99 en Windows 11): contenedores *healthy* en ≈ 27 s, rol `salesx_app` creado por `docker/03_aplicar_rol_app.sh`, prueba de humo 19/19, carga de 1 500 peticiones sin errores, persistencia tras reiniciar y restauración de respaldo (Evidencia 7). Falta repetirlo en el servidor de despliegue, el proxy TLS y los servicios reales de INTEGRAX (documento 05).

**Importante — HTTPS:** en producción la cookie de sesión es `Secure`: el navegador solo la envía por HTTPS (la excepción es `localhost`). Sin el proxy con TLS, el inicio de sesión por la interfaz web no se mantendrá desde otra máquina.

**Detener y limpiar:** `docker compose --env-file .env.docker down` conserva los datos; añadir `-v` **borra el volumen de la base de datos**.

En `ENVIRONMENT=production` la aplicación **no inicia** si: las claves son las de ejemplo o muy cortas, la contraseña del admin es débil, se usa SQLite o `SEED_DEMO_USERS=true`.

## 4. Variables de configuración

| Variable | Por defecto | Descripción |
|---|---|---|
| `ENVIRONMENT` | `development` | `production` activa validaciones y HSTS. |
| `DATABASE_URL` | `sqlite:///./sales_x.db` | `postgresql+psycopg2://usuario:clave@host:5432/salesx` en producción. |
| `SECRET_KEY` | (ejemplo) | Firma de los JWT. ≥ 32 caracteres. |
| `TOKEN_EXPIRE_MINUTES` | `480` | Duración de la sesión. |
| `INTEGRATION_API_KEY` | (ejemplo) | Clave del consumidor inicial «INTEGRAX-inicial» (se crea una sola vez si no hay consumidores). Las demás claves se gestionan en la pantalla *Integraciones*. |
| `IVA_RATE` | `0.19` | Tasa de impuesto. |
| `BUSINESS_TZ` | `America/Bogota` | Zona para filtros y reportes. |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_NAME` | — | Administrador inicial (se crea una vez). |
| `SEED_DEMO_USERS` | `true` | Crea el vendedor demo; `false` en producción. |
| `CATALOGO_PROVIDER` | `simulado` | `rest` consume los servicios reales. |
| `CLIENTES_API_URL`, `PRODUCTOS_API_URL` | — | URLs base de los microproyectos. |
| `INTEGRATION_TIMEOUT_SECONDS` | `5` | Tiempo máximo de espera a servicios externos. |
| `CORS_ORIGINS` | vacío | Orígenes permitidos (coma). Vacío = mismo origen. |

## 5. Integración con otros microproyectos

### 5.1 Consumir Clientes y Productos (`CATALOGO_PROVIDER=rest`)
Los servicios deben responder JSON con este contrato (ver E2 §7):
```
GET {CLIENTES_API_URL}        → [{"cliente_id","nombre","documento","correo"}]
GET {CLIENTES_API_URL}/{id}   → objeto cliente (404 si no existe)
GET {PRODUCTOS_API_URL}       → [{"producto_id","nombre","sku","precio","disponible","activo"}]
GET {PRODUCTOS_API_URL}/{id}  → objeto producto (404 si no existe)
```
Si un servicio no responde, tarda más de `INTEGRATION_TIMEOUT_SECONDS`, devuelve un error HTTP o una respuesta que no cumple este contrato (no es JSON, faltan campos, UUID o precio inválidos), SALES-X devuelve **502** y **no registra el pedido**; cuando el servicio vuelve, se recupera solo, sin reiniciar. Las consultas son en vivo (sin caché): SALES-X ve al instante los cambios de existencias.

**Probar sin los servicios reales** (servicios simulados que cumplen este contrato, solo para pruebas):
```bash
# Solo el servicio simulado, en local
python -m uvicorn mocks.integrax_mock:app --port 8001
#   luego, en .env:  CATALOGO_PROVIDER=rest
#                    CLIENTES_API_URL=http://localhost:8001/api/clientes
#                    PRODUCTOS_API_URL=http://localhost:8001/api/productos

# Todo en contenedores (API + PostgreSQL + servicio simulado)
docker compose -f docker-compose.yml -f docker-compose.mock.yml --env-file .env.docker up -d --build
```
El simulado publica el puerto 8001 con utilidades de prueba (`POST /_admin/modo` para provocar lentitud, error 500 o respuestas inválidas; `POST /_admin/productos/{id}` para cambiar existencias). **No usar en producción:** no tiene autenticación.

### 5.2 Servicios que SALES-X expone (cabecera `X-API-Key`)

**Una clave por sistema consumidor.** El administrador las crea en la pantalla *Integraciones* o por API (`POST /api/v1/consumidores`, con sesión de administrador); la clave se muestra **una sola vez** y se guarda solo su hash. Se pueden revocar, tienen expiración opcional y registran su último uso; las solicitudes que llegan quedan auditadas con el nombre del consumidor. Para rotar: crear una nueva, configurar el sistema y revocar la anterior.

| Método y ruta | Uso |
|---|---|
| `GET /api/v1/integracion/pedidos/{pedido_id}` | Consultar un pedido. |
| `GET /api/v1/integracion/clientes/{cliente_id}/pedidos` | Historial de un cliente. |
| `GET /api/v1/integracion/disponibilidad/{producto_id}` | Disponibilidad de un producto. |
| `POST /api/v1/integracion/pedidos/{pedido_id}/solicitudes` | Solicitud del cliente (`{"tipo":"cancelacion\|modificacion","detalle":"…"}`) → 202. |

Ejemplo:
```bash
curl -H "X-API-Key: <clave>" http://localhost:8000/api/v1/integracion/pedidos/<uuid>
```

## 6. Resumen de la API de usuario (`/api/v1`, Bearer JWT)

| Grupo | Endpoints |
|---|---|
| Autenticación | `POST /auth/login` (fija cookie `HttpOnly` + cookie CSRF y devuelve el JWT) · `POST /auth/logout` · `GET /auth/me` · `POST /auth/cambiar-contrasena` |
| Usuarios (admin) | `GET/POST /vendedores` · `PATCH /vendedores/{id}` |
| Consumidores de integración (admin) | `GET/POST /consumidores` · `PATCH /consumidores/{id}` |
| Pedidos | `POST/GET /pedidos` · `GET/PUT /pedidos/{id}` · `PATCH /pedidos/{id}/estado` · `POST /pedidos/{id}/cancelar` · `GET /pedidos/{id}/auditoria` · `GET /pedidos/historial/{cliente_id}` · `GET /pedidos/solicitudes` · `GET /estados` |
| Catálogo | `GET /catalogo/clientes` · `GET /catalogo/productos` · `GET /catalogo/productos/{id}/disponibilidad` |
| Reportes | `GET /reportes/ventas` · `GET /reportes/ventas.csv` |
| Operación | `GET /health` (sin autenticación) |

**Autenticación de los clientes:** el navegador usa la cookie de sesión y debe enviar `X-CSRF-Token` (valor de la cookie `salesx_csrf`) en POST/PUT/PATCH; un cliente de API usa `Authorization: Bearer <JWT>` y no necesita CSRF. Mientras un usuario deba cambiar su contraseña, toda la API responde 403 salvo `/auth/me`, `/auth/cambiar-contrasena` y `/auth/logout`.

Documentación interactiva completa: `/docs` (OpenAPI). El contrato exportado está en `specs/sales-x/openapi.json`.

## 7. Copias de seguridad y restauración (PostgreSQL)

```bash
# Respaldo diario (cron) — comprimido
docker compose exec -T db pg_dump -U salesx -Fc salesx > respaldo_$(date +%F).dump

# Restauración en una base vacía
docker compose exec -T db pg_restore -U salesx -d salesx --clean --if-exists < respaldo_AAAA-MM-DD.dump
```
Recomendaciones: retención de 30 días, copia fuera del servidor, **prueba de restauración trimestral** y cifrado de las copias. Las copias deben incluir `auditoria_pedido`.

> Estos comandos se ejecutaron en Docker (Git Bash): el respaldo se restauró tras borrar datos y la auditoría siguió protegida. **En PowerShell 5 el operador `>` corrompe los archivos binarios**: use Git Bash o WSL, o genere el archivo dentro del contenedor y cópielo con `docker compose cp` (variante no probada). Con `--env-file`, añádalo a cada comando `docker compose`.

## 8. Monitoreo y registros
- `GET /health` → 200 si la BD responde; 503 si no (úselo en el balanceador y en alertas).
- El contenedor tiene `HEALTHCHECK` y reinicio automático.
- Registros: `docker compose logs -f api`. Los errores internos se registran con traza; el cliente solo ve «Error interno del servidor».
- Indicadores sugeridos: ver `capacidad.md` §5.

## 8.1 Herramientas de documentación y verificación

| Script | Para qué |
|---|---|
| `scripts/generar_fragmentos.py` | Inventario, endpoints, licencias y registro de pruebas (`docs/fragmentos`). |
| `scripts/generar_diccionario.py` | Diccionario de datos a partir del modelo real. |
| `scripts/generar_mer.py` | Diagrama entidad-relación (SVG/PNG). |
| `scripts/capturas.py` | Capturas de pantalla (requiere `pip install playwright`). |
| `scripts/licencias.py` | Licencias de las dependencias. |
| `scripts/generar_pdf.py`, `scripts/generar_word.py` | PDF y Word de los documentos. |
| `scripts/verificar_documentacion.py` | Contrasta documentación y código. |
| `scripts/armar_entrega.py` | Reúne el paquete de entrega en `ENTREGA/`. |

## 9. Mantenimiento
| Tarea | Frecuencia |
|---|---|
| `pip-audit -r requirements.txt` y actualización de dependencias | Mensual |
| Revisar usuarios activos y roles | Trimestral |
| Rotar `SECRET_KEY` (cierra todas las sesiones) y las claves de los consumidores de integración | Semestral o ante sospecha |
| Revisar consumidores activos y su «último uso» (revocar los que ya no se usen) | Trimestral |
| Verificar espacio en disco y crecimiento de `auditoria_pedido` | Mensual |
| Prueba de restauración de respaldo | Trimestral |

## 10. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| La API no inicia en producción: «Configuración insegura…» | Claves por defecto, SQLite o usuarios demo | Corregir las variables indicadas en el mensaje. |
| `/health` devuelve 503 | BD no disponible o credenciales erróneas | Revisar `DATABASE_URL` y el estado de PostgreSQL. |
| 502 al registrar pedidos | Servicio de Clientes/Productos caído | Verificar `CLIENTES_API_URL`/`PRODUCTOS_API_URL`. |
| 401 en integración | Falta la cabecera `X-API-Key`, o la clave es errónea, está revocada o expiró | Enviar una clave vigente (crear otra en *Integraciones*). |
| 403 «Token CSRF inválido» | Una escritura por cookie sin la cabecera `X-CSRF-Token` | Enviar la cabecera con el valor de la cookie `salesx_csrf`, o usar `Bearer`. |
| 403 «Debe cambiar su contraseña» | Usuario nuevo o con contraseña restablecida | Llamar a `POST /auth/cambiar-contrasena` (la interfaz lo pide sola). |
| Reportes con fechas corridas | `BUSINESS_TZ` incorrecta | Ajustar la zona horaria de negocio. |
| 429 al ingresar | Bloqueo por intentos fallidos | Esperar 5 minutos. |
| `permission denied for table …` en los registros de la API | Tablas recreadas o nuevas sin permisos para `salesx_app` | Volver a ejecutar `sql/03_rol_aplicacion.sql` como superusuario. |
| `must be owner of table …` / `permission denied for schema` al iniciar | La API (rol limitado) intenta crear o alterar el esquema | Crear/migrar el esquema con el dueño (`sql/01`, `sql/04`) antes de iniciar la API. |
