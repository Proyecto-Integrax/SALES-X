# Capacidad y escalado · SALES-X 1.2.0

Documento de planificación de capacidad. Responde: **¿cuánta carga aguanta hoy SALES-X, qué se rompe primero y qué hacer cuando crezca?** Las cifras marcadas como *medidas* salen de ejecuciones reales (Evidencia 7); las marcadas como *supuestas* son hipótesis que deben validarse con datos de operación.

## 0. Cómo usar este documento

1. Lea la sección 1 para saber qué se supone del uso.
2. Compare su uso real con los escenarios de la sección 3.
3. Si cruza un umbral de la sección 4, aplique la acción de la sección 6.
4. Antes de cualquier decisión de infraestructura, **mida** (sección 5): no escale por intuición.

## 1. Supuestos

| Supuesto | Valor | Tipo |
|---|---|---|
| Usuarios internos (vendedores y administradores) | 5–50 | Supuesto |
| Pedidos por día | 50–2.000 | Supuesto |
| Líneas por pedido | 1–10 (media 3) | Supuesto |
| Horario de uso | Laboral, con picos de 1–2 h | Supuesto |
| Peticiones de INTEGRAX por pedido | 1 consulta + eventuales solicitudes | Supuesto |
| Tamaño por pedido en base de datos (con líneas y auditoría) | ≈ 2,4 KB | Medido |
| Despliegue | 1 contenedor de API + 1 de PostgreSQL en un único host | Real |

## 2. Diagnóstico actual (medido)

| Prueba | Entorno | Resultado |
|---|---|---|
| Carga mixta, 20 usuarios concurrentes, 500 peticiones | PostgreSQL local | p95 **0,098 s**, p99 0,389 s, 0 errores |
| Carga mixta, 25 usuarios, 1.500 peticiones | Docker (producción) | p95 **0,130 s**, p99 0,554 s, 0 errores |
| `POST /pedidos` completo con catálogo REST | Docker + simulador | ≈ **200 ms** |
| Consulta individual al catálogo REST | Cliente HTTP persistente | ≈ 0,9 ms (antes de DEF-05: 185 ms) |
| Rendimiento frente al RNF-01 (p95 < 3 s) | — | Holgura de ≈ 20 veces |

**Lectura:** con una hipótesis de 50 usuarios y 2.000 pedidos/día (≈ 0,02 pedidos/s en promedio; picos de 1–2 por segundo), el sistema trabaja a una fracción de su capacidad medida. **El cuello de botella actual no es la CPU ni la base de datos: son las llamadas en serie a servicios externos y los reportes calculados en memoria.**

**Límites de las mediciones:** una sola máquina de desarrollo, ráfagas cortas (no horas), servicios externos simulados y datos pequeños (cientos de pedidos). No prueban volumen alto ni latencias reales de red.

## 3. Escenarios

### Escenario A · Uso esperado (hasta ≈ 2.000 pedidos/día)
- **Almacenamiento:** 2.000 × 2,4 KB ≈ 4,8 MB/día ≈ **1,7 GB/año**.
- **Cómputo:** un contenedor de API basta con amplia holgura.
- **Riesgo principal:** los reportes. Con ≈ 700.000 pedidos/año, calcular ventas en memoria dejará de ser razonable.
- **Acción:** mantener la arquitectura; programar la mejora de reportes (sección 6) antes de superar ≈ 100.000 pedidos acumulados.

### Escenario B · Crecimiento (≈ 20.000 pedidos/día o integración intensiva)
- **Almacenamiento:** ≈ 17 GB/año; conviene particionar o archivar la auditoría de pedidos cerrados.
- **Cómputo:** varias réplicas de la API detrás de un balanceador (el diseño no guarda estado local; el bloqueo de fila funciona entre réplicas). **No probado.**
- **Riesgos:** consultas en serie al catálogo (latencia por pedido proporcional al número de líneas), concentración de escrituras sobre `auditoria_pedido`, y conexiones de base de datos (el *pool* por defecto es pequeño).
- **Acción:** paralelizar o agrupar las consultas al catálogo; pasar los reportes a SQL; separar réplica de lectura para reportes.

## 4. Umbrales de decisión

| Indicador | Verde | Atención | Acción |
|---|---|---|---|
| p95 de la API | < 0,5 s | 0,5–2 s | Revisar consultas lentas y servicios externos |
| Errores 5xx | < 0,1 % | 0,1–1 % | Revisar registros; ¿servicio externo caído? |
| Respuestas 502 (servicios externos) | < 1 % | > 1 % | Contactar al propietario del servicio; revisar tiempos de espera |
| CPU del contenedor de API | < 60 % | > 70 % sostenido | Añadir réplica |
| Conexiones de BD usadas | < 60 % del máximo | > 80 % | Ajustar *pool* o añadir *pooler* |
| Espacio en disco de BD | < 60 % | > 75 % | Ampliar o archivar |
| Pedidos acumulados | < 100.000 | > 100.000 | Reportes en SQL e índices adicionales |
| Tiempo de respaldo | < 5 min | > 15 min | Respaldo incremental / réplica |

## 5. Checklist de medición (antes de decidir nada)

- [ ] Registrar p50/p95/p99 por endpoint durante una semana laboral.
- [ ] Contar pedidos diarios y líneas por pedido reales (reemplazar los supuestos de la sección 1).
- [ ] Medir el tiempo de las llamadas a Clientes y Productos reales.
- [ ] Revisar el plan de ejecución (`EXPLAIN ANALYZE`) de las consultas de reportes con un volumen realista (≥ 100.000 pedidos de prueba).
- [ ] Probar la carga **sostenida** (≥ 1 hora) y de pico en el servidor real.
- [ ] Probar 2 réplicas de la API con la misma base y repetir las pruebas de concurrencia (CP-61 a CP-63).
- [ ] Registrar el crecimiento real de la base durante un mes.

## 6. Hoja de ruta de capacidad

| Orden | Mejora | Disparador | Esfuerzo |
|---|---|---|---|
| 1 | Proxy con TLS y límites de tasa (H-09, H-10) | Antes de exponer a Internet | 6–8 h |
| 2 | Consultar el catálogo **antes** de tomar el bloqueo de fila | Servicios externos lentos | 2–3 h |
| 3 | Reportes con `GROUP BY` en SQL | > 100.000 pedidos | 1 día |
| 4 | Índices adicionales según `EXPLAIN` | Consultas > 0,5 s | 2–4 h |
| 5 | Consultas en paralelo o por lote al catálogo | Pedidos con muchas líneas | 1 día |
| 6 | Varias réplicas de la API + balanceador | CPU > 70 % sostenida | 1–2 días |
| 7 | Archivar la auditoría de pedidos cerrados | > 10 GB de datos | 2 días |
| 8 | Alembic para migraciones versionadas | Antes de la siguiente versión | 1 día |

## 7. Qué NO hacer

- **No** escalar por intuición ni comprar infraestructura sin medir (sección 5).
- **No** añadir una caché del catálogo sin definir cómo se invalida: las existencias deben ser en vivo.
- **No** desactivar el bloqueo de fila «para ganar velocidad»: es lo que garantiza la máquina de estados.
- **No** usar SQLite fuera de la demostración.
- **No** dar a la aplicación un usuario de base de datos con permisos de propietario.
- **No** publicar el puerto de PostgreSQL.
- **No** guardar el respaldo solo en el mismo servidor.

## 8. Decisiones pendientes

| Decisión | Quién | Cuándo |
|---|---|---|
| Volumen real esperado de pedidos | Responsable de ventas | Antes de piloto |
| Retención de la auditoría (¿cuántos años?) | Responsable legal / ventas | Antes de producción |
| Servidor y proveedor de despliegue | Operaciones | Antes de producción |
| Disponibilidad exigida (¿99 %? ¿99,9 %?) | Responsable de ventas | Antes de producción |
| ¿Réplica de lectura para reportes? | Tech Lead | Si pedidos > 100.000 |

## 9. Referencias

- Evidencia 7 · Pruebas de integración: cargas, REST, Docker y concurrencia.
- Informe 01 · Auditoría de seguridad, sección de riesgos.
- Documento 05 · Revisión de lanzamiento (sección Tech Lead y DevOps).
- `scripts/carga_basica.py` para repetir la medición de carga.
