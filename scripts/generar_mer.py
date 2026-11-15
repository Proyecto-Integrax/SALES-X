"""Genera el diagrama entidad-relación (notación pata de gallo) a partir de las tablas REALES del programa.

Salida: docs/diagramas/mer-salesx.svg y .png (el PNG se obtiene con Edge/Chrome en modo headless).
Uso:    python scripts/generar_mer.py
"""

import html
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from sqlalchemy.dialects import postgresql  # noqa: E402

import app.models  # noqa: E402,F401
from app.database import Base  # noqa: E402

SALIDA = RAIZ / "docs" / "diagramas"
NUCLEO = {"pedido", "detalle_pedido", "estado_pedido"}
# (x, y) de la esquina superior izquierda de cada tabla
POS = {
    "estado_pedido": (30, 40),
    "pedido": (440, 40),
    "detalle_pedido": (880, 40),
    "vendedor": (440, 400),
    "auditoria_pedido": (880, 330),
    "intento_login": (30, 400),
    "consumidor_api": (30, 560),
}
ANCHO, ALTO_CAB, ALTO_FILA = 330, 32, 24
# relaciones: (tabla_hija, columna_fk, lado_hija, lado_padre)
# (lado en la tabla hija, lado en la padre, fracción a lo largo del lado hija, fracción en la padre): evita que dos
# conexiones lleguen al mismo punto
LADOS = {
    ("pedido", "estado_id"): ("l", "r", 0.5, 0.5),
    ("pedido", "vendedor_id"): ("b", "t", 0.25, 0.25),
    ("detalle_pedido", "pedido_id"): ("l", "r", 0.5, 0.5),
    ("auditoria_pedido", "pedido_id"): ("t", "b", 0.5, 0.75),
    ("auditoria_pedido", "vendedor_id"): ("l", "r", 0.5, 0.5),
}


def tipo(col) -> str:
    t = col.type.compile(dialect=postgresql.dialect())
    return t.replace("TIMESTAMP WITH TIME ZONE", "TIMESTAMPTZ").replace("VARCHAR", "varchar").replace(" ", "").lower().replace("timestamptz", "timestamptz")


def alto(tabla) -> int:
    return ALTO_CAB + ALTO_FILA * len(tabla.columns) + 6


def ancla(nombre, lado, tablas, frac=0.5):
    x, y = POS[nombre]
    h = alto(tablas[nombre])
    return {"l": (x, y + h * frac), "r": (x + ANCHO, y + h * frac), "t": (x + ANCHO * frac, y), "b": (x + ANCHO * frac, y + h)}[lado]


def ruta(p1, l1, p2, l2):
    (x1, y1), (x2, y2) = p1, p2
    if l1 in "lr" and l2 in "lr":
        xm = (x1 + x2) / 2
        return [(x1, y1), (xm, y1), (xm, y2), (x2, y2)]
    if l1 in "tb" and l2 in "tb":
        ym = (y1 + y2) / 2
        return [(x1, y1), (x1, ym), (x2, ym), (x2, y2)]
    if l1 in "lr":
        return [(x1, y1), (x2, y1), (x2, y2)]
    return [(x1, y1), (x1, y2), (x2, y2)]


def pata_de_gallo(p, hacia):
    """Tres líneas que parten de un punto en la dirección `hacia` (vector unitario)."""
    x, y = p
    dx, dy = hacia
    px, py = -dy, dx  # perpendicular
    largo, ancho = 16, 8
    bx, by = x + dx * largo, y + dy * largo
    return [(bx + px * ancho, by + py * ancho, x, y), (bx, by, x, y), (bx - px * ancho, by - py * ancho, x, y)]


def main():
    tablas = Base.metadata.tables
    svg = []
    W, H = 1260, 900
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Segoe UI, Arial, sans-serif">')
    svg.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
    svg.append('<text x="30" y="26" font-size="16" font-weight="700" fill="#16367f">Modelo Entidad-Relación · SALES-X (7 tablas, PostgreSQL)</text>')

    # relaciones primero (quedan detrás de las tablas)
    lineas = []
    for nombre, t in tablas.items():
        for fk in t.foreign_keys:
            col = fk.parent
            padre = fk.column.table.name
            lado_h, lado_p, f_h, f_p = LADOS[(nombre, col.name)]
            ph, pp = ancla(nombre, lado_h, tablas, f_h), ancla(padre, lado_p, tablas, f_p)
            pts = ruta(ph, lado_h, pp, lado_p)
            d = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
            lineas.append(f'<polyline points="{d}" fill="none" stroke="#5a6478" stroke-width="1.6"/>')
            # extremo hijo (pata de gallo) y extremo padre (barra / opcional)
            def dir_salida(p_ini, p_sig):
                vx, vy = p_sig[0] - p_ini[0], p_sig[1] - p_ini[1]
                n = max(abs(vx), abs(vy)) or 1
                return (vx / n, vy / n)
            dh = dir_salida(pts[0], pts[1])
            dp = dir_salida(pts[-1], pts[-2])
            for x1, y1, x2, y2 in pata_de_gallo(pts[0], dh):
                lineas.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#5a6478" stroke-width="1.6"/>')
            opcional = col.nullable
            lineas.append(f'<text x="{pts[0][0] + dh[0] * 26 - 6:.0f}" y="{pts[0][1] + dh[1] * 26 - 6:.0f}" font-size="12" font-weight="700" fill="#16367f">{"0..N" if opcional else "N"}</text>')
            lineas.append(f'<text x="{pts[-1][0] + dp[0] * 22 - 6:.0f}" y="{pts[-1][1] + dp[1] * 22 - 6:.0f}" font-size="12" font-weight="700" fill="#16367f">{"0..1" if opcional else "1"}</text>')
    svg.extend(lineas)

    # tablas
    for nombre, t in tablas.items():
        x, y = POS[nombre]
        h = alto(t)
        color = "#16367f" if nombre in NUCLEO else "#6b7488"
        svg.append(f'<rect x="{x}" y="{y}" width="{ANCHO}" height="{h}" rx="6" fill="#fff" stroke="{color}" stroke-width="1.8"/>')
        svg.append(f'<path d="M{x},{y + 6} a6,6 0 0 1 6,-6 h{ANCHO - 12} a6,6 0 0 1 6,6 v{ALTO_CAB - 6} h-{ANCHO} z" fill="{color}"/>')
        svg.append(f'<text x="{x + 12}" y="{y + 21}" font-size="14" font-weight="700" fill="#fff">{html.escape(nombre)}</text>')
        svg.append(f'<text x="{x + ANCHO - 10}" y="{y + 21}" font-size="10" text-anchor="end" fill="#dbe3f5">{"núcleo" if nombre in NUCLEO else "soporte"} · {len(t.columns)} columnas</text>')
        fks = {c.name for c in t.columns if c.foreign_keys}
        for i, c in enumerate(t.columns):
            yy = y + ALTO_CAB + i * ALTO_FILA
            if c.primary_key:
                svg.append(f'<rect x="{x + 1}" y="{yy + 1}" width="{ANCHO - 2}" height="{ALTO_FILA}" fill="#e8eefc"/>')
            marca = "PK" if c.primary_key else ("FK" if c.name in fks else "")
            if marca:
                svg.append(f'<text x="{x + 10}" y="{yy + 17}" font-size="11" font-weight="700" fill="{"#16367f" if marca == "PK" else "#a86400"}">{marca}</text>')
            peso = "700" if c.primary_key else "400"
            svg.append(f'<text x="{x + 40}" y="{yy + 17}" font-size="12.5" font-weight="{peso}" fill="#1b2333">{html.escape(c.name)}{"" if not c.nullable or c.primary_key else " ?"}</text>')
            svg.append(f'<text x="{x + ANCHO - 10}" y="{yy + 17}" font-size="11.5" text-anchor="end" fill="#5a6478" font-family="Consolas, monospace">{html.escape(tipo(c))}</text>')

    # leyenda
    ly = H - 70
    svg.append(f'<rect x="30" y="{ly}" width="{W - 60}" height="56" rx="6" fill="#f4f6fb" stroke="#dbe3f5"/>')
    svg.append(f'<text x="44" y="{ly + 22}" font-size="12" fill="#1b2333"><tspan font-weight="700">Notación pata de gallo:</tspan> 1 = exactamente uno · N = muchos · 0..1 / 0..N = opcional (la FK admite NULL) · «?» junto al nombre = columna que admite NULL.</text>')
    svg.append(f'<text x="44" y="{ly + 42}" font-size="12" fill="#1b2333"><tspan font-weight="700">Colores:</tspan> azul = núcleo del negocio (pedidos) · gris = soporte (usuarios, auditoría, seguridad, integración). <tspan font-weight="700">cliente_id</tspan> y <tspan font-weight="700">producto_id</tspan> son referencias lógicas a otros microproyectos (sin FK).</text>')
    svg.append("</svg>")

    SALIDA.mkdir(parents=True, exist_ok=True)
    svg_path = SALIDA / "mer-salesx.svg"
    svg_path.write_text("\n".join(svg), encoding="utf-8")

    # PNG con el navegador (2x para nitidez)
    exe = next((p for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe") if Path(p).exists()), None)
    if exe:
        pagina = SALIDA / "_mer_tmp.html"
        pagina.write_text(f'<!doctype html><meta charset="utf-8"><body style="margin:0">{svg_path.read_text(encoding="utf-8")}</body>', encoding="utf-8")
        png = SALIDA / "mer-salesx.png"
        subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2", f"--window-size={W},{H}", f"--screenshot={png}", pagina.as_uri()], check=True, capture_output=True, timeout=90)
        pagina.unlink(missing_ok=True)
        print("OK ", png.name, f"({png.stat().st_size // 1024} KB)")
    print("OK ", svg_path.name)


if __name__ == "__main__":
    main()
