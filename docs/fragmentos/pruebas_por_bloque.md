| Bloque de pruebas | Archivo | Pruebas | Resultado |
|---|---|---:|---|
| Núcleo de la API: autenticación, pedidos, estados, reportes, integración, seguridad básica | `tests/test_api.py` | 27 | Aprobadas |
| Validación de la configuración de producción | `tests/test_config.py` | 2 | Aprobadas |
| Zona horaria de negocio (reportes por día) | `tests/test_timeutil.py` | 2 | Aprobadas |
| Endurecimiento: bloqueo en BD, consumidores, cookie + CSRF, contraseñas | `tests/test_endurecimiento.py` | 15 | Aprobadas |
| Integración REST con Clientes y Productos (servicio HTTP simulado) | `tests/test_catalogo_rest.py` | 14 | Aprobadas |
| tests/test_concurrencia.py | `tests/test_concurrencia.py` | 3 | Aprobadas |
| **Total** | | **63** | **63 aprobadas, 0 fallidas** |
