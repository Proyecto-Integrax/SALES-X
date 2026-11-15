# Estado de remediación de la auditoría · SALES-X 1.2.0

Seguimiento de los hallazgos del informe `01-Informe-Auditoria-Seguridad-SALES-X.md`. Corte: **14 de noviembre de 2026**.

**Resumen:** 14 hallazgos · **9 remediados y verificados** · **4 abiertos** · 1 informativo que cumple. No hay hallazgos críticos ni altos abiertos. Evolución: 13/11 → 3 remediados; 14/11 → 9 remediados.

## 1. Críticos

Ninguno.

## 2. Altos

### H-01 · Secretos por defecto — ✅ Remediado
- **Qué se hizo:** `validate_for_production` en `app/config.py`: con `ENVIRONMENT=production` la aplicación no arranca con claves por defecto o cortas, contraseña de administrador débil, SQLite o usuarios demo. `docker-compose.yml` exige cada secreto.
- **Cómo se verificó:** CP-28 y CP-29; arranque en Docker en modo producción con secretos aleatorios; los `.bat` de arranque generan los suyos.

### H-14 · Carrera en los cambios de estado — ✅ Remediado
- **Qué se hizo:** `SELECT … FOR UPDATE` al cargar el pedido en modificar, cambiar de estado y cancelar (`app/services/pedidos.py`, `app/routers/pedidos.py`); el estado se carga después del bloqueo.
- **Cómo se verificó:** CP-61 a CP-63: 30 rondas cada una sobre PostgreSQL (antes, 29 de 30 rondas violaban la máquina de estados); estables en 5 ejecuciones seguidas.
- **Nota:** en SQLite (solo demostración) el bloqueo no existe; estas pruebas se omiten allí.

## 3. Medios

### H-02 · Sin HSTS — ✅ Remediado
- **Qué se hizo:** cabecera `Strict-Transport-Security` en producción (1 año, subdominios). **Verificación:** observada en Docker.

### H-03 · Errores sin registro — ✅ Remediado
- **Qué se hizo:** `log.error(..., exc_info=exc)` con método y ruta, sin exponer la traza al cliente. **Verificación:** registros de la API sin errores inexplicados tras la carga.

### H-04 · Bloqueo de login en memoria — ✅ Remediado
- **Qué se hizo:** tabla `intento_login` y servicio `app/services/login_throttle.py`; 5 fallos en 5 minutos → 429, compartido entre instancias. **Verificación:** CP-32, CP-33.

### H-05 · Token en `sessionStorage` — ✅ Remediado
- **Qué se hizo:** cookie `HttpOnly` + `SameSite=Strict` (+ `Secure` en producción) y token CSRF *double submit*; la interfaz no guarda el token. **Verificación:** CP-39 a CP-42 y recorrido en el navegador.
- **Riesgo residual:** un XSS podría actuar con la sesión (no robarla); lo limitan la CSP y el escape de salida.

### H-06 · Clave de integración única — ✅ Remediado
- **Qué se hizo:** tabla `consumidor_api` (hash SHA-256, activo, expiración, último uso), endpoints `/consumidores` y pantalla *Integraciones*; «INTEGRAX-inicial» se crea desde `INTEGRATION_API_KEY`. **Verificación:** CP-34 a CP-38.

### H-13 · Auditoría no inmutable a nivel de base de datos — ✅ Remediado
- **Qué se hizo:** `sql/03_rol_aplicacion.sql` crea `salesx_app` (sin esquema, sin `UPDATE`/`DELETE`/`TRUNCATE` sobre la auditoría); `.env` de desarrollo y `docker-compose.yml` lo usan; `docker/03_aplicar_rol_app.sh` lo crea al inicializar la base.
- **Cómo se verificó:** 9 de 9 comprobaciones de permisos y 11 de 11 pasos de la API con ese rol en PostgreSQL; verificado también en Docker.
- **Defecto hallado al verificar (DEF-03):** el script inicial daba permisos por defecto y, tras **restaurar un respaldo**, el rol recuperaba `UPDATE`/`DELETE` sobre la auditoría. Se eliminaron los permisos por defecto; la restauración repetida dio el resultado correcto (también en la base local ya existente, tras reejecutar el script).
- **Pendiente:** aplicarlo en la base del entorno objetivo y reejecutarlo tras crear tablas nuevas.

### H-09 · Sin TLS propio — ⛔ Abierto
- **Estado:** pendiente. Es el único hallazgo que bloquea una salida a producción.
- **Evidencia del impacto:** en Docker (modo producción) la cookie `Secure` no se reenvía por HTTP plano; sin proxy con TLS el inicio de sesión no se mantiene fuera de `localhost`.
- **Próxima acción:** proxy inverso (Nginx o Traefik) con certificado y redirección a HTTPS. *~4–6 h.*

## 4. Bajos

### H-07 · Gestión de contraseñas — ✅ Remediado
- **Qué se hizo:** política de ≥ 10 caracteres con letras y números, sin comunes ni el usuario; cambio propio con bloqueo por intentos; cambio obligatorio en el primer ingreso y tras un restablecimiento. **Verificación:** CP-43 a CP-46 y recorrido en el navegador.

### H-08 · `/docs` público — ⛔ Abierto
- **Próxima acción:** ocultarlo o restringirlo por red en producción. *~0,5 h.*

### H-10 · Sin límites de tasa ni de tamaño — ⛔ Abierto
- **Próxima acción:** `limit_req` y `client_max_body_size` en el proxy. *~1–2 h.*

### H-12 · Sin revocación de tokens al cerrar sesión — ⛔ Abierto
- **Estado:** cerrar sesión borra las cookies, pero un JWT copiado seguiría válido hasta expirar (8 h). Un usuario inactivo queda bloqueado al instante.
- **Próxima acción:** tokens de 15–30 minutos con renovación revocable. *~6–8 h.*

## 5. Pendiente y por qué

| Pendiente | Por qué sigue abierto | Quién puede cerrarlo |
|---|---|---|
| H-09, H-10, H-08 | Dependen del **entorno de despliegue** (proxy inverso), que no existe en el equipo de desarrollo. | Operaciones, al desplegar |
| H-12 | Requiere rediseñar la sesión (tokens cortos con renovación); es de severidad baja y la cookie ya limita su explotación. | Desarrollo, en la siguiente iteración |
| Aplicar `sql/03` en la base real | Depende de tener esa base. | Operaciones / DBA |
| Probar con los servicios reales de INTEGRAX | Los otros microproyectos aún no existen. | Todo el curso, al integrarse |

## 6. Cómo se verificó

1. **Pruebas automáticas:** cada hallazgo corregido tiene al menos una prueba (63 en total) que fallaba antes de la corrección cuando fue posible demostrarlo (H-14: 29 de 30 rondas; DEF-04: tres pruebas).
2. **Doble motor:** la suite se ejecuta en SQLite y en PostgreSQL; los hallazgos que dependen de PostgreSQL (H-13, H-14) se verifican allí.
3. **Docker en producción:** arranque desde cero, humo de 19 pasos, integración REST de 14 pasos, persistencia y restauración de respaldo.
4. **Recorridos en el navegador:** sesión (`document.cookie`, CSRF, cierre de sesión) y cambio obligatorio de contraseña, con capturas en la Evidencia 7.
5. **Coherencia documentación-código:** `python scripts/verificar_documentacion.py` contrasta lo que dicen estos documentos con el programa.

### Defectos funcionales corregidos durante la auditoría (no de seguridad)

| ID | Descripción | Estado |
|---|---|---|
| DEF-01 | Reportes vacíos para pedidos de la noche (fechas interpretadas en UTC) | ✅ |
| DEF-02 | Diálogos de la interfaz dependían solo del evento `close` | ✅ |
| DEF-03 | Tras restaurar un respaldo, el rol recuperaba permisos sobre la auditoría | ✅ |
| DEF-04 | Respuestas inválidas del servicio externo producían error 500 | ✅ |
| DEF-05 | Cada consulta al catálogo REST tardaba ≈ 185 ms | ✅ |
| DEF-06 | En móvil la página se salía de la pantalla | ✅ |
| DEF-07 | Carrera en los cambios de estado (es H-14) | ✅ |
