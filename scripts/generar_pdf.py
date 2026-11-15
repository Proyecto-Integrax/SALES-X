"""Genera los PDF de docs/ a partir de docs/fuentes/*.md usando Microsoft Edge/Chrome (modo headless).

Uso:  python scripts/generar_pdf.py
Requiere:  pip install markdown   y   Edge o Chrome instalado.
Portada: si el .md trae `evidencia:` en su cabecera se genera una portada como la de las evidencias (ver _comun.py).
"""

import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _comun as C  # noqa: E402

FUENTES = C.DOCS / "fuentes"
SALIDA = C.DOCS

NAVEGADORES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Roboto, Arial, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #1b2333; }
.portada { background: #2457d6; color: #fff; padding: 14px 18px; border-radius: 8px; margin-bottom: 18px; }
.portada .cod { font-size: 9pt; letter-spacing: .08em; opacity: .85; }
.portada .tit { font-size: 15pt; font-weight: 700; margin-top: 2px; }
.cover { min-height: 255mm; display: flex; flex-direction: column; page-break-after: always; padding-top: 6mm; }
.cover .marca { font-size: 30pt; font-weight: 800; letter-spacing: .06em; color: #16367f; }
.cover .sub { font-size: 12pt; color: #5a6478; margin-top: 2px; }
.cover .ev { margin-top: 38mm; display: inline-block; align-self: flex-start; background: #e8eefc; color: #16367f; font-weight: 700; font-size: 10pt; padding: 3px 12px; border-radius: 99px; letter-spacing: .05em; }
.cover h1 { font-size: 27pt; line-height: 1.12; margin: 10px 0 12px; color: #16367f; }
.cover .desc { font-size: 11.5pt; color: #33405a; max-width: 150mm; }
.cover table.meta { margin-top: 14mm; width: 150mm; font-size: 10.5pt; }
.cover table.meta td { border: 0; border-bottom: 1px solid #dbe3f5; padding: 6px 4px; }
.cover table.meta td:first-child { color: #5a6478; width: 52mm; }
.cover table.meta td:last-child { font-weight: 600; }
.cover .aut { margin-top: auto; font-size: 9pt; letter-spacing: .15em; color: #5a6478; font-weight: 700; }
.cover .nom { font-size: 12pt; font-weight: 600; margin-top: 3px; }
.cover .linea { margin-top: 8mm; padding-top: 6px; border-top: 2px solid #2457d6; font-size: 9pt; color: #5a6478; }
.pie-doc { margin-top: 18px; padding-top: 6px; border-top: 1px solid #dbe3f5; font-size: 8.5pt; color: #5a6478; }
h1 { font-size: 20pt; margin: 0 0 8px; color: #16367f; }
h2 { font-size: 13.5pt; margin: 20px 0 8px; color: #16367f; border-bottom: 1.5px solid #dbe3f5; padding-bottom: 3px; page-break-after: avoid; }
h3 { font-size: 11.5pt; margin: 14px 0 6px; color: #1f3f94; page-break-after: avoid; }
p { margin: 6px 0; }
table { width: 100%; border-collapse: collapse; margin: 8px 0 12px; font-size: 9.2pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { background: #e8eefc; color: #16367f; text-align: left; padding: 5px 7px; border: 1px solid #c9d4ef; }
td { padding: 5px 7px; border: 1px solid #d9e0ee; vertical-align: top; }
code { font-family: Consolas, 'Courier New', monospace; font-size: 9pt; background: #f0f3fa; padding: 1px 4px; border-radius: 3px; }
pre { background: #f4f6fb; border: 1px solid #dbe3f5; border-radius: 6px; padding: 9px 11px; overflow: hidden; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 8.8pt; }
blockquote { margin: 8px 0; padding: 6px 12px; border-left: 4px solid #f0b04b; background: #fff7e6; color: #5c4510; }
img { max-width: 100%; display: block; margin: 8px auto; border: 1px solid #ccd5ea; border-radius: 6px; }
em { color: #44506a; }
ul, ol { margin: 6px 0 6px 20px; padding: 0; }
hr { border: 0; border-top: 1px solid #dbe3f5; margin: 14px 0; }
.nw { white-space: nowrap; }
"""


def navegador() -> str:
    for ruta in NAVEGADORES:
        if Path(ruta).exists():
            return ruta
    sys.exit("No se encontró Edge/Chrome. Instale uno o ajuste NAVEGADORES en este script.")


def portada(meta: dict, fuente: Path) -> str:
    if meta.get("evidencia"):
        filas = "".join(f"<tr><td>{html.escape(a)}</td><td>{html.escape(v)}</td></tr>" for a, v in C.filas_meta(meta))
        return (
            '<section class="cover">'
            f'<div class="marca">{C.SISTEMA.replace("-", "·")}</div><div class="sub">{C.DESCRIPCION_SISTEMA}</div>'
            f'<div class="ev">Evidencia {html.escape(meta["evidencia"])}</div>'
            f'<h1>{html.escape(meta.get("titulo", fuente.stem))}</h1>'
            f'<p class="desc">{html.escape(meta.get("descripcion", ""))}</p>'
            f'<table class="meta">{filas}</table>'
            f'<div class="aut">AUTORES</div><div class="nom">{html.escape(C.autores())}</div>'
            f'<div class="linea">{html.escape(C.linea_proyecto())}</div></section>'
        )
    return (
        f'<div class="portada"><div class="cod">{meta.get("codigo", "SALES-X")} · SALES-X · Integración de Aplicaciones</div>'
        f'<div class="tit">{html.escape(meta.get("titulo", fuente.stem))}</div></div>'
    )


def main() -> None:
    exe = navegador()
    # nl2br: respeta los saltos de línea escritos (p. ej. las casillas ☐ del acta, una por renglón)
    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "nl2br"])
    for fuente in sorted(FUENTES.glob("*.md")):
        meta, cuerpo = C.separar_front_matter(fuente.read_text(encoding="utf-8"))
        md.reset()
        cuerpo_html = md.convert(C.expandir(cuerpo))
        # Los identificadores (CU-01, RF-03, H-04…) no deben partirse en dos líneas dentro de las tablas.
        cuerpo_html = re.sub(r"\b(?:RNF|RF|CU|CP|DEF|EV|RN|CA|HU|H|S|UAT)-\d{1,2}\b", lambda m: f'<span class="nw">{m.group(0)}</span>', cuerpo_html)
        pie = f'<div class="pie-doc">{html.escape(meta["pie"])}</div>' if meta.get("pie") else ""
        titulo = meta.get("titulo", fuente.stem)
        pagina = f'<!doctype html><html lang="es"><meta charset="utf-8"><title>{html.escape(titulo)}</title><style>{CSS}</style><body>{portada(meta, fuente)}{cuerpo_html}{pie}</body></html>'
        tmp = FUENTES / f"_tmp_{fuente.stem}.html"
        tmp.write_text(pagina, encoding="utf-8")
        pdf = SALIDA / f"{fuente.stem}.pdf"
        try:
            subprocess.run(
                [exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", tmp.as_uri()],
                check=True, capture_output=True, timeout=120,
            )
        finally:
            tmp.unlink(missing_ok=True)
        print(f"OK  {pdf.name}  ({pdf.stat().st_size // 1024} KB)")
    shutil.rmtree(FUENTES / "__pycache__", ignore_errors=True)


if __name__ == "__main__":
    main()
