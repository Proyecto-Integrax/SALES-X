"""Captura la interfaz web real de SALES-X para la evidencia visual (docs/capturas/*.png).

Levanta la aplicación sobre una base SQLite temporal con datos de demostración, la recorre con Edge (Playwright) y
guarda las capturas. No toca ninguna base real.

Requiere:  pip install playwright     (usa el Edge instalado; no descarga navegadores)
Uso:       python scripts/capturas.py
"""

import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "docs" / "capturas"
PUERTO = 8765
BASE = f"http://127.0.0.1:{PUERTO}"


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{(tmp / 'capturas.db').as_posix()}", "ENVIRONMENT": "development", "SEED_DEMO_USERS": "true",
           "ADMIN_EMAIL": "admin@salesx.local", "ADMIN_PASSWORD": "Admin2026*", "PYTHONIOENCODING": "utf-8"}
    subprocess.run([sys.executable, "-m", "app.demo"], cwd=RAIZ, env=env, check=True, capture_output=True)
    srv = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(PUERTO), "--host", "127.0.0.1"], cwd=RAIZ, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                if httpx.get(f"{BASE}/health", timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.5)
        # usuario nuevo (para mostrar el cambio obligatorio de contraseña)
        tok = httpx.post(f"{BASE}/api/v1/auth/login", json={"correo": "admin@salesx.local", "contrasena": "Admin2026*"}).json()["access_token"]
        nuevo = f"ana.perez{uuid.uuid4().hex[:3]}@empresa.com"
        httpx.post(f"{BASE}/api/v1/vendedores", headers={"Authorization": f"Bearer {tok}"}, json={"nombre": "Ana Pérez", "correo": nuevo, "contrasena": "Inicial2026x"})

        with sync_playwright() as pw:
            nav = pw.chromium.launch(channel="msedge", headless=True)
            ctx = nav.new_context(viewport={"width": 1280, "height": 800}, locale="es-CO", timezone_id="America/Bogota", color_scheme="light")
            pag = ctx.new_page()

            def foto(nombre, completa=False):
                pag.wait_for_timeout(500)
                pag.screenshot(path=str(SALIDA / f"{nombre}.png"), full_page=completa)
                print("OK ", nombre)

            def entrar(correo, clave):
                pag.goto(BASE)
                pag.fill("#l-correo", correo)
                pag.fill("#l-pass", clave)
                pag.click("#login-form button[type=submit]")
                pag.wait_for_selector("#shell:not(.hidden)", timeout=15000)

            pag.goto(BASE)
            pag.wait_for_selector("#login:not(.hidden)")
            foto("01-inicio-de-sesion")

            entrar("vendedor@salesx.local", "Ventas2026*")
            pag.wait_for_selector(".kpi")
            foto("02-panel")

            pag.goto(f"{BASE}/#/pedidos")
            pag.wait_for_selector("table")
            foto("03-pedidos")

            pag.goto(f"{BASE}/#/nuevo")
            pag.wait_for_selector("#f-cliente")
            pag.select_option("#f-cliente", index=1)
            for i in (1, 2):
                pag.select_option("#f-prod", index=i)
                pag.fill("#f-qty", "2")
                pag.click("#f-add")
            pag.fill("#f-desc", "Entrega en bodega principal")
            foto("04-nuevo-pedido")
            pag.click("#f-save")
            pag.wait_for_selector(".timeline")
            pag.click("[data-state]")  # primer botón de cambio de estado
            pag.wait_for_selector("#dlg[open]")
            pag.fill("#d-com", "Confirmado con el cliente por teléfono")
            pag.click("#dlg-ok")
            pag.wait_for_timeout(900)
            foto("05-detalle-y-auditoria", completa=True)

            pag.goto(f"{BASE}/#/reportes")
            pag.wait_for_selector(".bars")
            foto("06-reporte-de-ventas")

            # vista móvil
            movil = ctx.new_page()
            movil.set_viewport_size({"width": 390, "height": 844})
            movil.goto(BASE)
            movil.wait_for_selector("#shell:not(.hidden)")
            movil.wait_for_selector(".kpi")
            movil.wait_for_timeout(500)
            movil.screenshot(path=str(SALIDA / "07-vista-movil.png"))
            print("OK  07-vista-movil")
            # Comprobación de desbordamiento horizontal en pantalla de 390 px (la página no debe salirse de la ventana)
            desbordes = []
            for ruta in ("dashboard", "pedidos", "nuevo", "reportes"):
                movil.goto(f"{BASE}/#/{ruta}")
                movil.wait_for_timeout(700)
                ancho = movil.evaluate("document.documentElement.scrollWidth")
                if ancho > 390:
                    desbordes.append((ruta, ancho))
            print("DESBORDE HORIZONTAL EN MÓVIL:", desbordes or "ninguno")
            movil.goto(BASE)
            movil.close()

            ctx.clear_cookies()
            entrar("admin@salesx.local", "Admin2026*")
            pag.goto(f"{BASE}/#/usuarios")
            pag.wait_for_selector("table")
            foto("08-usuarios")
            pag.goto(f"{BASE}/#/integraciones")
            pag.wait_for_selector("#cf")
            foto("09-integraciones")

            ctx.clear_cookies()
            pag.goto(BASE)
            pag.fill("#l-correo", nuevo)
            pag.fill("#l-pass", "Inicial2026x")
            pag.click("#login-form button[type=submit]")
            pag.wait_for_selector("#dlg[open]")
            foto("10-cambio-obligatorio-de-contrasena")
            nav.close()
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=10)
        except subprocess.TimeoutExpired:
            srv.kill()


if __name__ == "__main__":
    main()
