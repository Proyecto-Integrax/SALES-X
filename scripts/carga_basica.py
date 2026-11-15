"""Prueba de carga básica contra una instancia en ejecución (RNF-01: respuesta < 3 s).

Uso:  python scripts/carga_basica.py [URL] [USUARIOS_CONCURRENTES] [PETICIONES_POR_USUARIO]
Requiere el servidor levantado y un usuario válido: por defecto el vendedor de demostración (SEED_DEMO_USERS=true);
en otros entornos defina SALESX_USER y SALESX_PASS. Crea pedidos reales: úselo en entornos de prueba.
"""

import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
USERS = int(sys.argv[2]) if len(sys.argv) > 2 else 20
REQS = int(sys.argv[3]) if len(sys.argv) > 3 else 25
API = BASE + "/api/v1"

# Credenciales: variables SALESX_USER / SALESX_PASS (por defecto, el vendedor de demostración).
USER = os.environ.get("SALESX_USER", "vendedor@salesx.local")
PASS = os.environ.get("SALESX_PASS", "Ventas2026*")
tok = httpx.post(f"{API}/auth/login", json={"correo": USER, "contrasena": PASS}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}
cliente = httpx.get(f"{API}/catalogo/clientes", headers=H).json()[0]["cliente_id"]
producto = next(p for p in httpx.get(f"{API}/catalogo/productos", headers=H).json() if p["disponible"] > 50)["producto_id"]


def escenario(client: httpx.Client, i: int):
    out = []
    for n in range(REQS):
        t = time.perf_counter()
        k = (i + n) % 4
        if k == 0:
            r, tipo = client.get(f"{API}/pedidos?size=20", headers=H), "GET /pedidos"
        elif k == 1:
            r, tipo = client.get(f"{API}/reportes/ventas", headers=H), "GET /reportes/ventas"
        elif k == 2:
            r, tipo = client.get(f"{API}/catalogo/productos", headers=H), "GET /catalogo/productos"
        else:
            r, tipo = client.post(f"{API}/pedidos", headers=H, json={"cliente_id": cliente, "items": [{"producto_id": producto, "cantidad": 1}]}), "POST /pedidos"
        out.append((tipo, time.perf_counter() - t, r.status_code))
    return out


def main():
    t0 = time.perf_counter()
    with ThreadPoolExecutor(USERS) as ex, httpx.Client(timeout=30) as client:
        resultados = [x for lote in ex.map(lambda i: escenario(client, i), range(USERS)) for x in lote]
    total = time.perf_counter() - t0
    tiempos = sorted(r[1] for r in resultados)
    errores = sum(1 for r in resultados if r[2] >= 400)
    p = lambda q: tiempos[min(len(tiempos) - 1, int(len(tiempos) * q))]  # noqa: E731
    print(f"Usuarios concurrentes: {USERS} | Peticiones: {len(resultados)} | Duración: {total:.1f}s | Rendimiento: {len(resultados) / total:.1f} req/s")
    print(f"Errores HTTP: {errores}")
    print(f"Latencia (s): media={statistics.mean(tiempos):.3f}  p50={p(.5):.3f}  p95={p(.95):.3f}  p99={p(.99):.3f}  max={tiempos[-1]:.3f}")
    for tipo in sorted({r[0] for r in resultados}):
        t = sorted(r[1] for r in resultados if r[0] == tipo)
        print(f"  {tipo:<26} n={len(t):<4} media={statistics.mean(t):.3f}s  p95={t[int(len(t) * .95) - 1]:.3f}s")
    print("RNF-01 (<3 s en el p95):", "CUMPLE" if p(.95) < 3 else "NO CUMPLE")


if __name__ == "__main__":
    main()
