# Metodología y evidencias — Auditoría de seguridad SALES-X

Documento de apoyo del informe `01-Informe-Auditoria-Seguridad-SALES-X.md`. Explica **cómo** se hizo la revisión y deja las evidencias para que un tercero pueda repetirla.

## 1. Preparación y control de integridad

| Elemento | Detalle |
|---|---|
| Sistema | SALES-X 1.0.0 (línea base, 13/11/2026) y 1.2.0 (reverificación, 14/11/2026) |
| Equipo de pruebas | Windows 11 Pro · Python 3.13 · PostgreSQL 18.6 local · Docker Desktop 4.99 (motor 29.9.3, Compose v5.7) |
| Bases de datos usadas | SQLite temporal, PostgreSQL local (`salesx_test` para pruebas, `salesx` para la aplicación) y PostgreSQL 16 en contenedor |
| Control de versiones | **El proyecto aún no está bajo Git**; no hay *commit* que citar. Para compensarlo, la sección 2 incluye la **huella SHA-256** de cada archivo revisado: quien tenga los mismos archivos obtendrá las mismas huellas. |
| Datos | Solo datos de demostración y de prueba; ninguna base de producción |
| Secretos | Los de las pruebas son aleatorios o de demostración; los de Docker se generan aleatorios y no se publican |

**Control de integridad:** las huellas se generan con `python scripts/generar_fragmentos.py` (sección 2). Si un archivo cambia después de la revisión, su huella cambia.

## 2. Inventario de la superficie revisada

{{incluir: fragmentos/inventario_codigo.md}}

Además de los archivos fuente, se revisaron los **7 tablas** del modelo, las **31 operaciones** HTTP expuestas (tabla del informe, sección 3.3) y la **imagen Docker** `sales-x-api` (29 paquetes de Python).

## 3. Comandos ejecutados

Todos se ejecutan desde la carpeta `sales-x`. Los que escriben datos lo hacen solo en bases de prueba (`salesx_test` o bases temporales).

```
# 1. Inventario de archivos, endpoints, tablas y huellas
python scripts/generar_fragmentos.py
python scripts/generar_diccionario.py

# 2. Pruebas automatizadas (63) en SQLite y en PostgreSQL
python -m pytest -v
set TEST_DATABASE_URL=postgresql+psycopg2://salesx:CLAVE@localhost:5432/salesx_test
python -m pytest -v
#   Resultado: SQLite 60 aprobadas + 3 omitidas (concurrencia); PostgreSQL 63 aprobadas

# 3. Dependencias
python -m pip_audit -r requirements.txt
python scripts/licencias.py
#   Resultado: "No known vulnerabilities found"; 29 paquetes, 7 licencias

# 4. Validación de los scripts SQL sobre PostgreSQL vacío
psql -U salesx -d salesx_test -f sql/01_schema.sql -f sql/02_seed_estados.sql
python -m pytest        # (con TEST_KEEP_SCHEMA=1: usa el esquema creado por el SQL)

# 5. Rol de mínimo privilegio
psql -U postgres -d salesx -v app_password=... -f sql/03_rol_aplicacion.sql
psql -U salesx_app -d salesx -c "UPDATE auditoria_pedido SET accion = accion;"   # -> permission denied

# 6. Respaldo y restauración
pg_dump -Fc -f respaldo.dump salesx
pg_restore --clean --if-exists -d salesx respaldo.dump
#   Resultado: datos recuperados; el rol sigue sin poder editar la auditoría

# 7. Docker en modo producción
docker compose --env-file .env.docker up -d --build
docker compose -f docker-compose.yml -f docker-compose.mock.yml --env-file .env.docker up -d --build

# 8. Carga
python scripts/carga_basica.py http://127.0.0.1:8000 20 25
```

## 4. Resultado bruto de `pip-audit`

{{incluir: fragmentos/pip_audit.md}}

El equivalente a `npm audit` de los ejemplos de otros proyectos: aquí se audita `requirements.txt` (las 9 dependencias directas y su árbol).

## 5. Criterios de clasificación

La severidad combina **impacto** (qué se pierde) y **facilidad de explotación** (qué necesita el atacante).

| Severidad | Criterio | Ejemplo en este proyecto |
|---|---|---|
| Crítica | Compromiso total y remoto sin autenticación. | (ninguno) |
| Alta | Compromiso de cuentas o de la integridad de datos con poco esfuerzo, o explotable en uso normal. | H-01 secretos por defecto; H-14 carrera en estados |
| Media | Debilidad explotable bajo condiciones específicas, o que reduce otras defensas. | H-04, H-05, H-06, H-09, H-13 |
| Baja | Endurecimiento o riesgo menor. | H-07, H-08, H-10, H-12 |
| Informativa | Observación o cumplimiento. | H-11 |

**Estados:** ✅ *Remediado* (corregido y con prueba o evidencia) · ⛔ *Abierto* (pendiente) · *Cumple* (no requería acción).

## 6. Qué NO se hizo (límites de esta revisión)

- No se hizo una **prueba de penetración dinámica** con herramientas externas (OWASP ZAP, Burp) ni análisis estático automático (Bandit, Semgrep).
- No se auditaron los servicios reales de Clientes y Productos, que aún no existen.
- No se probó en un **servidor real** ni con TLS: el entorno fue una máquina de desarrollo con Docker Desktop.
- No se realizaron pruebas de **denegación de servicio** ni de volumen sostenido; la carga fue de 500 a 1.500 peticiones.
- No hubo **revisión independiente**: auditor y desarrollador son el mismo equipo.
- No se revisó el texto completo de las licencias de terceros.
- La revisión visual cubrió Edge en escritorio y en pantalla estrecha (390 px); no otros navegadores.

## 7. Cómo reproducir esta auditoría

1. Obtener la misma versión del código y comprobar las huellas SHA-256 de la sección 2.
2. Crear una base PostgreSQL de pruebas (`salesx_test`) y ejecutar los comandos 2 a 6 de la sección 3.
3. Levantar Docker con los comandos del punto 7 y repetir los recorridos de la Evidencia 7 (§7.3 y §7.4).
4. Comparar los resultados con los de este informe y con `docs/fragmentos/registro_pruebas.md` (registro completo de la ejecución).
5. Comprobar la coherencia documentación-código con `python scripts/verificar_documentacion.py`.

## 8. Trazabilidad hallazgo → evidencia

| Hallazgo | Evidencia que lo demuestra | Dónde |
|---|---|---|
| H-01 Secretos por defecto | Pruebas CP-28 y CP-29; arranque en producción en Docker | `tests/test_config.py`; Evidencia 7 §7.3 |
| H-02 Sin HSTS | Cabecera observada en producción | Evidencia 7 §7.3 |
| H-03 Errores sin registro | Registro con traza; 0 errores inexplicados | Registros de la API |
| H-04 Bloqueo en memoria | CP-32, CP-33 | `tests/test_endurecimiento.py` |
| H-05 Token legible | CP-39 a CP-42; `document.cookie` en el navegador | Evidencia 7 §6 |
| H-06 Clave única | CP-34 a CP-38 | `tests/test_endurecimiento.py` |
| H-07 Contraseñas | CP-43 a CP-46 | `tests/test_endurecimiento.py` |
| H-09 TLS | Cookie `Secure` no enviada por HTTP plano | Evidencia 7 §7.3 |
| H-11 Dependencias | `pip-audit` | Sección 4 |
| H-13 Auditoría inmutable | Permisos del rol y restauración de respaldo | Evidencia 7 §7.2 y §7.3 |
| H-14 Carrera en estados | CP-61, CP-62, CP-63 (29 de 30 rondas fallaban antes) | `tests/test_concurrencia.py` |
| H-08, H-10, H-12 | Sin evidencia de corrección: están abiertos | Informe 01, sección 5.4 |

## 9. Declaración final

El equipo declara que este informe describe con fidelidad lo que se revisó, cómo se revisó y con qué límites. Los hallazgos corregidos lo fueron con cambios al código que quedan cubiertos por pruebas; los abiertos se declaran como tales. Esta revisión es un control interno y no sustituye una auditoría independiente.
