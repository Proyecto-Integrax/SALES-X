# SALES-X · Gestión de Ventas y Pedidos

Microproyecto de **INTEGRAX** (Integración de Aplicaciones · Unisabaneta). Aplicación web + API REST para registrar, gestionar y reportar pedidos de venta, construida a partir de los seguimientos 1 y 2 (TDR, fichas técnicas, requerimientos, casos de uso, UML y modelo de datos).

| | |
|---|---|
| **Lenguaje / framework** | Python 3.12+ · FastAPI · SQLAlchemy |
| **Base de datos** | PostgreSQL (producción) · SQLite (desarrollo local, sin instalar nada) |
| **Interfaz** | Web responsiva en JavaScript puro (sin dependencias ni CDN) |
| **Integración** | REST/JSON · JWT para usuarios · `X-API-Key` para sistemas · consumo REST de Clientes y Productos |
| **Despliegue** | Docker + docker-compose (`docker compose --env-file .env.docker up -d --build`; ver la guía §3) |

## Demostración en línea (GitHub Pages)

La carpeta `docs/` publica la interfaz real con una **API simulada en el navegador** (`app/static/demo-api.js`): se puede iniciar sesión, crear y modificar pedidos, cambiar estados, ver la auditoría y el reporte, sin servidor ni base de datos (los datos viven en el navegador; hay botón «Restablecer datos»). La documentación está en `docs/documentos.html`. Para regenerarla tras cambiar la interfaz: `python scripts/publicar_pages.py`.

## Cómo ejecutarlo (elija una opción)

| Opción | Qué necesita | Cómo | Qué obtiene |
|---|---|---|---|
| **A · Local (la más simple)** | Python 3.12+ | Doble clic en **`iniciar.bat`** (Windows) o `bash iniciar.sh` (Linux/macOS) | Base SQLite con **40 pedidos de demostración** y usuarios listos; abre el navegador solo |
| **B · Docker** (modo producción) | Docker Desktop abierto | Doble clic en **`iniciar-docker.bat`** | API + PostgreSQL en contenedores, con secretos aleatorios generados automáticamente; base vacía |

En ambas: **http://localhost:8000**. Los usuarios de demostración de la opción A están abajo; en la B, el administrador es `admin@salesx.local` y su contraseña está en el archivo `.env.docker` (valor `ADMIN_PASSWORD`).

## Inicio rápido manual (opción A, paso a paso)

Equivale a `iniciar.bat`:

```bash
python -m pip install -r requirements.txt
python -m app.demo                       # base SQLite con 40 pedidos de demostración
python -m uvicorn app.main:app --port 8000
```

Abra <http://localhost:8000> · API interactiva en <http://localhost:8000/docs>

| Usuario | Correo | Contraseña (solo demo) |
|---|---|---|
| Administrador | `admin@salesx.local` | `Admin2026*` |
| Vendedor | `vendedor@salesx.local` | `Ventas2026*` |

## Qué hace

Registrar pedidos (cliente + productos, **IVA y totales automáticos**) · modificar y cancelar · **estados con reglas de transición y bloqueo de fila (sin carreras)** · **auditoría** de cada operación · historial por cliente · **reporte de ventas** (día/mes, CSV) · consulta de **disponibilidad** · **servicios de integración** (incl. solicitudes de cancelación/modificación del cliente) · administración de usuarios.

**Seguridad (v1.2):** sesión en cookie `HttpOnly` con protección CSRF · bloqueo de login compartido en la base de datos · **una clave de integración por sistema** (revocable, con expiración y último uso) · política de contraseñas y **cambio obligatorio en el primer ingreso**.

**Actualizar desde la v1.0:** `sql/04_migracion_v1_1.sql` (conserva los datos; ver la guía de operación).

**Base de datos de mínimo privilegio:** la API se conecta como `salesx_app` (`sql/03_rol_aplicacion.sql`): no altera el esquema y no puede modificar ni borrar la auditoría. Migraciones, datos de demostración y pruebas con PostgreSQL usan el dueño (`salesx`); ver la guía §2.2.

## Estructura

```
sales-x/
├── app/                 API: routers/ (HTTP) · services/ (reglas de negocio) · models.py · integration/ · static/ (UI)
├── sql/                 Esquema PostgreSQL, estados iniciales, rol de mínimo privilegio y migración v1.0→v1.1
├── tests/               63 pruebas automatizadas (pytest; 3 de concurrencia solo en PostgreSQL)
├── mocks/               Servicios simulados de Clientes y Productos (para probar la integración REST)
├── scripts/             Carga, documentación (PDF, Word, diagramas, capturas, fragmentos) y verificación
├── specs/               Especificaciones de trabajo: requirements.md · design.md · tasks.md
├── docs/                Documentación formal (fuentes en docs/fuentes; paquete final en ../ENTREGA)
├── Dockerfile · docker-compose.yml · .env.example · iniciar.bat · iniciar.sh · iniciar-docker.bat · iniciar-docker.sh
```

## Pruebas

```bash
python -m pytest -v          # 63 pruebas: 60 en SQLite + 3 de concurrencia que se omiten

# Sobre PostgreSQL (la base debe terminar en "_test"; ver la Guía de operación §2.1)
set TEST_DATABASE_URL=postgresql+psycopg2://salesx:CLAVE@localhost:5432/salesx_test
python -m pytest -v          # 63 de 63
```

## Documentación

Estructura equivalente al proyecto de referencia FINAN-X, con contenido propio de SALES-X. Las fuentes están en `docs/fuentes/`; el paquete listo para enviar se arma con `python scripts/armar_entrega.py` en la carpeta `ENTREGA/` (PDF, Markdown y `Word/`).

| Archivo | Contenido |
|---|---|
| `E1_Modelo_Entidad_Relacion.pdf` | Modelo E-R (diagrama generado del código), relaciones y reglas de integridad |
| `E2_Diccionario_de_Datos.pdf` | Tablas, columnas, tipos, restricciones y dominios (41 campos) |
| `E3_ERS_IEEE830.pdf` | Especificación de requerimientos (IEEE 830) |
| `E4_Matriz_Propiedad_Intelectual.pdf` | Titularidad y licencias de dependencias (29 paquetes) |
| `E5_Contrato_Licencia_Software.pdf` | Modelo de contrato de licencia |
| `E6_Matriz_Trazabilidad.pdf` | Requerimiento → componente → prueba (CP-01…CP-63) |
| `E7_Pruebas_Integracion.pdf` | Casos de prueba, defectos, carga, Docker, REST y capturas |
| `Acta-Usuarios-Primer-Ingreso.pdf` | Acta de entrega de cuentas |
| `01-Informe-Auditoria-Seguridad-SALES-X.md` | 14 hallazgos de seguridad |
| `03-Metodologia-y-Evidencias.md` | Método, comandos y huellas SHA-256 |
| `04-Estado-de-Remediacion.md` | Seguimiento de hallazgos |
| `05-Revision-Lanzamiento-GO-NO-GO.md` | Revisión de lanzamiento por roles |
| `capacidad.md` | Capacidad y escalado |
| `Manual-de-Usuario.md` · `Guia-de-Operacion-y-Despliegue.md` | Extras: uso, instalación, API, respaldos |

Para contrastar los documentos con el código: `python scripts/verificar_documentacion.py`.

## Estado de verificación (14/11/2026, versión 1.2.0)

- ✅ 63/63 pruebas automáticas en PostgreSQL y 60/60 (+3 omitidas) en SQLite · `pip-audit` limpio · carga sin errores (p95 0,098 s en PostgreSQL y 0,130 s en Docker) · respaldo y restauración · rol de BD de mínimo privilegio · 9 de 14 hallazgos de seguridad remediados, sin críticos ni altos abiertos · 7 defectos funcionales corregidos (incluida una carrera en los cambios de estado, ahora cubierta por 3 pruebas de concurrencia).
- ✅ Docker Compose en modo producción desde cero (humo 19/19) e integración REST contra servicios simulados (14/14).
- ⏳ **No ejecutado:** servicios **reales** de Clientes/Productos, TLS/proxy inverso (H-09) y repetición en un servidor de despliegue. Detalle en `docs/fuentes/05-Revision-Lanzamiento-GO-NO-GO.md`.