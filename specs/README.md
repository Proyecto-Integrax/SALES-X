# Specs — desarrollo guiado por especificaciones

SALES-X sigue el flujo **requisitos → diseño → tareas**: primero se define *qué* debe hacer el sistema, luego *cómo* se construye y por último *en qué pasos*. Cada paso es un archivo revisable antes de programar.

```
specs/
└── sales-x/
    ├── requirements.md   QUÉ: historias de usuario + criterios de aceptación (formato EARS)
    ├── design.md         CÓMO: arquitectura, datos, API, errores, seguridad, pruebas, decisiones
    ├── tasks.md          PASOS: lista de tareas trazable a requisitos y pruebas (hechas y pendientes)
    └── openapi.json      CONTRATO de la API (30 operaciones, 31 esquemas), exportado del código
```

## Cómo usarlas
1. **Cambio nuevo** → agregue o ajuste primero los requisitos (con ID nuevo, p. ej. `REQ-14`) y sus criterios.
2. Refleje la decisión técnica en `design.md` (y, si es una decisión importante, en la sección de decisiones).
3. Descomponga en tareas en `tasks.md`, cada una con los requisitos que cubre y la prueba que la verifica.
4. Implemente tarea por tarea, marcando `[x]` solo cuando la prueba pase.

## Formato EARS de los criterios
`CUANDO <evento> ENTONCES el sistema DEBERÁ <respuesta>` · `SI <condición> ENTONCES el sistema DEBERÁ <respuesta>` · `MIENTRAS <estado> el sistema DEBERÁ <respuesta>`.

## Relación con la documentación formal
Las specs son el documento **de trabajo del equipo** (se modifican con el código). Los documentos de `docs/` son los **entregables formales** y se derivan de ellas:

| Spec | Documento formal equivalente |
|---|---|
| `requirements.md` | `docs/E3_ERS_IEEE830.pdf` |
| `design.md` | `docs/E1`, `docs/E2`, `docs/Guia-de-Operacion-y-Despliegue.md` |
| `tasks.md` (trazabilidad y estado) | `docs/E6_Matriz_Trazabilidad.pdf`, `docs/05-Revision-Lanzamiento-GO-NO-GO.md` |

> Nota: estas specs se redactaron **después** de construir la primera versión (a partir de E3, E6 y el código verificado). Para los cambios futuros, el orden correcto es el inverso: spec primero.
