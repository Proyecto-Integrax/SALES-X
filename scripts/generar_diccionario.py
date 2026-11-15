"""Genera el diccionario de datos (docs/fragmentos/diccionario.md) desde las tablas REALES del programa.

Los datos técnicos (tipo, longitud, PK, FK, obligatoriedad) se leen del modelo; las descripciones de negocio viven en
este archivo y se validan contra el esquema: NO puede existir una columna sin documentar ni una descripción que hable de
una columna inexistente (el generador falla).

Uso:  python scripts/generar_diccionario.py
"""

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from sqlalchemy.dialects import postgresql  # noqa: E402

import app.models  # noqa: E402,F401
from app.database import Base  # noqa: E402

SALIDA = RAIZ / "docs" / "fragmentos" / "diccionario.md"  # carpeta de salida (se escriben dos archivos)

ENTIDADES = {
    "estado_pedido": ("Catálogo cerrado de estados del ciclo de vida del pedido: Pendiente, Confirmado, En preparación, Enviado, Entregado y Cancelado. Define las etapas que recorre un pedido.", "núcleo"),
    "pedido": ("Cabecera de una venta: a quién se vende, quién la registró, en qué estado está y cuánto suma. Sus importes los calcula siempre el servidor a partir de los precios del catálogo.", "núcleo"),
    "detalle_pedido": ("Líneas del pedido: un registro por producto y cantidad. Resuelve la relación de muchos a muchos entre pedidos y productos y congela el precio aplicado en el momento de la venta.", "núcleo"),
    "vendedor": ("Usuarios internos de SALES-X (vendedores y administradores). Es quien registra y gestiona los pedidos y quien firma cada evento de auditoría.", "soporte"),
    "auditoria_pedido": ("Bitácora de solo-agregar de todo lo que ocurre sobre un pedido (crear, modificar, cambiar de estado, cancelar, solicitudes del cliente). El rol de base de datos de la API no puede modificarla ni borrarla.", "soporte"),
    "intento_login": ("Fallos de inicio de sesión (y de cambio de contraseña) usados para bloquear temporalmente a quien se equivoca 5 veces en 5 minutos. Vive en la base de datos para que el bloqueo valga entre varias instancias y tras reinicios.", "soporte"),
    "consumidor_api": ("Sistemas de INTEGRAX que consumen los servicios de integración de SALES-X. Cada uno tiene su propia clave, que se guarda como huella (hash) y se puede revocar o dejar expirar.", "soporte"),
}

D = {
    ("estado_pedido", "estado_id"): "Identificador único del estado. Clave primaria.",
    ("estado_pedido", "nombre"): "Nombre del estado (Pendiente, Confirmado, En preparación, Enviado, Entregado, Cancelado). Único.",
    ("estado_pedido", "descripcion"): "Explicación breve de lo que significa el estado.",
    ("vendedor", "vendedor_id"): "Identificador único del usuario. Clave primaria.",
    ("vendedor", "nombre"): "Nombre completo del usuario; es el que aparece en la auditoría.",
    ("vendedor", "correo"): "Correo electrónico en minúscula; sirve como nombre de usuario para ingresar. Único.",
    ("vendedor", "contrasena"): "Contraseña cifrada con bcrypt (nunca en texto plano ni devuelta por la API).",
    ("vendedor", "rol"): "Perfil de autorización: «vendedor» (opera pedidos) o «admin» (además gestiona usuarios e integraciones).",
    ("vendedor", "activo"): "Si es falso, el usuario no puede ingresar ni operar. Se desactiva en lugar de borrar para conservar la trazabilidad.",
    ("vendedor", "debe_cambiar_contrasena"): "Verdadero cuando la contraseña la conoce el administrador (usuario nuevo o restablecida): el usuario debe definir una propia antes de operar.",
    ("pedido", "pedido_id"): "Identificador único del pedido. Clave primaria.",
    ("pedido", "cliente_id"): "Cliente al que se vende. Identificador común de INTEGRAX: la ficha del cliente vive en otro microproyecto, por eso no es clave foránea.",
    ("pedido", "estado_id"): "Estado actual del pedido. Clave foránea a estado_pedido.",
    ("pedido", "vendedor_id"): "Usuario que registró el pedido. Clave foránea a vendedor.",
    ("pedido", "subtotal"): "Suma de los subtotales de las líneas, sin impuestos. Lo calcula siempre el servidor.",
    ("pedido", "impuestos"): "IVA del pedido: subtotal × tasa configurada (19 %), redondeado a 2 decimales.",
    ("pedido", "descripcion"): "Observaciones libres sobre el pedido (por ejemplo, instrucciones de entrega).",
    ("pedido", "total"): "subtotal + impuestos. Calculado y verificado en el servidor; el navegador nunca envía importes.",
    ("pedido", "fecha_creacion"): "Momento en que se registró el pedido, en UTC. Los reportes lo interpretan en la zona horaria de negocio (America/Bogota).",
    ("detalle_pedido", "detalle_pedido_id"): "Identificador único de la línea. Clave primaria.",
    ("detalle_pedido", "pedido_id"): "Pedido al que pertenece la línea. Clave foránea a pedido, con borrado en cascada.",
    ("detalle_pedido", "producto_id"): "Producto vendido. Identificador común de INTEGRAX (el catálogo de productos vive en otro microproyecto; no es clave foránea).",
    ("detalle_pedido", "cantidad"): "Unidades vendidas; entero mayor que cero (la API admite de 1 a 10.000).",
    ("detalle_pedido", "precio_unitario"): "Precio vigente del catálogo al registrar el pedido. Se conserva como dato histórico aunque el catálogo cambie después.",
    ("detalle_pedido", "subtotal"): "cantidad × precio_unitario, redondeado a 2 decimales.",
    ("auditoria_pedido", "auditoria_id"): "Identificador único del evento. Clave primaria.",
    ("auditoria_pedido", "pedido_id"): "Pedido sobre el que ocurrió el evento. Clave foránea a pedido, con borrado en cascada.",
    ("auditoria_pedido", "vendedor_id"): "Usuario que realizó la acción. Admite NULL: las solicitudes del cliente llegan por integración, sin usuario interno.",
    ("auditoria_pedido", "fecha"): "Momento del evento, en UTC.",
    ("auditoria_pedido", "descripcion"): "Detalle legible del evento (por ejemplo «Pendiente -> Confirmado. Motivo…» o el total anterior y el nuevo).",
    ("auditoria_pedido", "accion"): "Tipo de evento: CREAR, MODIFICAR, CAMBIO_ESTADO, CANCELAR, SOLICITUD_MODIFICACION o SOLICITUD_CANCELACION.",
    ("intento_login", "intento_id"): "Identificador único del intento fallido. Clave primaria.",
    ("intento_login", "clave"): "Correo en minúscula (o «pw:» + correo cuando el fallo fue al cambiar la contraseña). Con ella se cuenta cuántos fallos lleva cada cuenta.",
    ("intento_login", "fecha"): "Momento del fallo, en UTC. Solo cuentan los de los últimos 5 minutos; los de más de 10 se borran solos.",
    ("consumidor_api", "consumidor_id"): "Identificador único del consumidor. Clave primaria.",
    ("consumidor_api", "nombre"): "Nombre del sistema consumidor (por ejemplo «INTEGRAX-inicial»). Único.",
    ("consumidor_api", "clave_hash"): "Huella SHA-256 de la clave. La clave en claro se muestra una sola vez al crearla y no se guarda. Única.",
    ("consumidor_api", "activo"): "Si es falso, la clave está revocada y deja de autenticar.",
    ("consumidor_api", "expira"): "Fecha de expiración opcional; pasada esa fecha la clave deja de valer.",
    ("consumidor_api", "creado"): "Fecha de creación del consumidor.",
    ("consumidor_api", "ultimo_uso"): "Última vez que la clave autenticó una petición (sirve para detectar claves en desuso).",
}


def tipo_y_longitud(col) -> tuple[str, str]:
    t = col.type.compile(dialect=postgresql.dialect())
    base = t.split("(")[0].upper().replace("TIMESTAMP WITH TIME ZONE", "TIMESTAMPTZ")
    longitud = "—"
    if "(" in t:
        longitud = t[t.index("(") + 1:t.index(")")].replace(" ", "")
    return base, longitud


def main():
    tablas = Base.metadata.tables
    # Validación: sin columnas sin documentar ni descripciones sobrantes
    reales = {(t, c.name) for t, tabla in tablas.items() for c in tabla.columns}
    faltan, sobran = sorted(reales - set(D)), sorted(set(D) - reales)
    sin_entidad = sorted(set(tablas) - set(ENTIDADES))
    if faltan or sobran or sin_entidad:
        sys.exit(f"Diccionario inconsistente.\n  Columnas sin describir: {faltan}\n  Descripciones de columnas inexistentes: {sobran}\n  Tablas sin descripción: {sin_entidad}")

    orden = ["estado_pedido", "vendedor", "pedido", "detalle_pedido", "auditoria_pedido", "intento_login", "consumidor_api"]
    md = ["| Entidad | Qué representa | Campos | Clave primaria | FK | Oblig. |", "|---|---|---:|---|---:|---:|"]
    for n in orden:
        t = tablas[n]
        fks = sum(1 for c in t.columns if c.foreign_keys)
        oblig = sum(1 for c in t.columns if not c.nullable)
        md.append(f"| `{n}` | {ENTIDADES[n][0].split('.')[0]}. | {len(t.columns)} | `{[c.name for c in t.primary_key][0]}` | {fks} | {oblig} |")
    md += ["", "*Total: " + f"{len(orden)} tablas y {sum(len(tablas[n].columns) for n in orden)} campos.*"]
    ent = []
    for i, n in enumerate(orden, 1):
        t = tablas[n]
        ent += [f"## 3.{i}. {n}", "", ENTIDADES[n][0], "", "| Campo | Tipo | Long. | PK | FK | Oblig. | Descripción |", "|---|---|---|---|---|---|---|"]
        for c in t.columns:
            tipo, lon = tipo_y_longitud(c)
            fk = ", ".join(f"{f.column.table.name}.{f.column.name}" for f in c.foreign_keys) or "No"
            ent.append(f"| `{c.name}` | {tipo} | {lon} | {'Sí' if c.primary_key else 'No'} | {fk} | {'Sí' if not c.nullable else 'No'} | {D[(n, c.name)]} |")
        ent.append("")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    (SALIDA.parent / "diccionario_panorama.md").write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    (SALIDA.parent / "diccionario_entidades.md").write_text("\n".join(ent).rstrip() + "\n", encoding="utf-8")
    print(f"OK  diccionario_panorama.md + diccionario_entidades.md · {len(orden)} tablas · {sum(len(tablas[n].columns) for n in orden)} campos, todos documentados")


if __name__ == "__main__":
    main()
