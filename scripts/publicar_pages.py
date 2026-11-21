"""Prepara la demostración para GitHub Pages: copia la interfaz (app/static) a docs/ junto con la API simulada.

Uso:  python scripts/publicar_pages.py     (después, git add docs && git commit && git push)
Pages debe servir la rama main, carpeta /docs. docs/documentos.html es la página de documentación (no se toca).
"""

import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN, DESTINO = RAIZ / "app" / "static", RAIZ / "docs"

for nombre in ("app.js", "styles.css", "demo-api.js"):
    shutil.copy2(ORIGEN / nombre, DESTINO / nombre)

html = (ORIGEN / "index.html").read_text(encoding="utf-8")
html = html.replace('<script src="app.js"></script>', '<script src="demo-api.js"></script>\n  <script src="app.js"></script>')
html = html.replace('<a class="small muted" id="lnk-docs" href="/docs" target="_blank" rel="noopener">API (Swagger)</a>',
                    '<a class="small muted" id="lnk-docs" href="documentos.html">Documentación</a>')
(DESTINO / "index.html").write_text(html, encoding="utf-8")
print("Demostración generada en", DESTINO)
