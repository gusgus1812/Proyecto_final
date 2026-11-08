#!/usr/bin/env python3
"""
Prueba del descargador (scripts/05_descargar_pozos_arcgis.py) contra un servidor ArcGIS
SIMULADO en tu propia computadora (no necesita internet). Comprueba paginacion, filtro por
campo, descubrimiento de capas, fechas y coordenadas.

Uso:  python3 tests/test_05_arcgis_simulado.py
"""
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "scripts" / "05_descargar_pozos_arcgis.py"
MS = 1627776000000  # 2021-08-01

POZOS = [  # (objectid, pozo, campo, estado, x, y)
    (1, "IXACHI-1", "IXACHI", "PRODUCTOR", -95.90, 18.40), (2, "IXACHI-35DES", "IXACHI", "PRODUCTOR", -95.91, 18.41),
    (3, "IXACHI-2", "IXACHI", "TAPONADO", -95.92, 18.42), (4, "AKAL-1", "AKAL", "CERRADO", -92.05, 19.85),
    (5, "AKAL-2", "AKAL", "PRODUCTOR", -92.06, 19.86), (6, "ZAMA-1", "ZAMA", "ABANDONADO", -93.50, 18.85),
    (7, "SIN-CAMPO-1", "", "EN ESPERA", None, None), (8, "TRION-1", "TRION", "PRODUCTOR", -96.70, 24.60)]
META = {"name": "Pozos simulados", "geometryType": "esriGeometryPoint", "maxRecordCount": 3,
        "fields": [{"name": "objectid", "type": "esriFieldTypeOID"}, {"name": "pozo", "type": "esriFieldTypeString"},
                   {"name": "campo", "type": "esriFieldTypeString"}, {"name": "estado_act", "type": "esriFieldTypeString"},
                   {"name": "fecha_inic", "type": "esriFieldTypeDate"}]}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _resp(self, obj):
        b = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _handle(self, params):
        ruta = urllib.parse.urlparse(self.path).path
        pag = ruta.startswith("/pag/")
        if ruta.endswith("/FeatureServer"):
            return self._resp({"layers": [{"id": 0, "name": "Pozos"}, {"id": 1, "name": "Otra capa (sin pozo)"}]})
        if re.search(r"/FeatureServer/1$", ruta):
            return self._resp({"name": "Otra", "geometryType": "esriGeometryPolygon", "fields": [], "maxRecordCount": 3})
        if ruta.endswith("/FeatureServer/0"):
            return self._resp({**META, "advancedQueryCapabilities": {"supportsPagination": pag}})
        if ruta.endswith("/query"):
            rows = POZOS
            w = params.get("where", "1=1")
            m = re.search(r"IN \((.*)\)", w)
            if m:
                vals = re.findall(r"'((?:[^']|'')*)'", m.group(1))
                rows = [r for r in rows if r[2] in vals]
            if params.get("objectIds"):
                ids = {int(i) for i in params["objectIds"].split(",")}
                rows = [r for r in rows if r[0] in ids]
            if params.get("returnIdsOnly") == "true":
                return self._resp({"objectIdFieldName": "objectid", "objectIds": [r[0] for r in rows]})
            off, n = int(params.get("resultOffset", 0)), int(params.get("resultRecordCount", 1000))
            trozo = rows[off:off + n] if pag else rows[:3] if not params.get("objectIds") else rows
            feats = [{"attributes": {"objectid": r[0], "pozo": r[1], "campo": r[2] or None, "estado_act": r[3], "fecha_inic": MS},
                      **({"geometry": {"x": r[4], "y": r[5]}} if r[4] is not None else {})} for r in trozo]
            return self._resp({"features": feats, "exceededTransferLimit": pag and off + n < len(rows)})
        self.send_error(404)

    def do_GET(self):
        self._handle({k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).items()})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        self._handle({k: v[0] for k, v in urllib.parse.parse_qs(self.rfile.read(n).decode()).items()})


def correr(url, *extra):
    with tempfile.TemporaryDirectory() as d:
        sal = Path(d) / "p.csv"
        env = {**os.environ, "NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost"}
        r = subprocess.run([sys.executable, "-I", str(SCRIPT), url, "--salida", str(sal), *extra],
                           capture_output=True, text=True, env=env)
        filas = list(csv.DictReader(open(sal, encoding="utf-8-sig"))) if sal.exists() else []
        return r.returncode, filas, r.stdout + r.stderr


def comprobar(nombre, cond, detalle=""):
    print(("OK   " if cond else "FALLA"), nombre, detalle)
    return cond


srv = HTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_port}"
ok = True
for modo in ("pag", "nopag"):
    rc, f, out = correr(f"{base}/{modo}/svc/FeatureServer")
    ok &= comprobar(f"[{modo}] descarga todo y pagina (max 3 por peticion)", rc == 0 and len(f) == 8, f"filas={len(f)}")
    ok &= comprobar(f"[{modo}] omite la capa que no es de pozos", "se omite" in out)
    ok &= comprobar(f"[{modo}] coordenadas y fecha ISO", f and f[0]["lon"] == "-95.9" and f[0]["lat"] == "18.4" and f[0]["fecha_inic"] == "2021-08-01")
    rc, f, out = correr(f"{base}/{modo}/svc/FeatureServer/0", "--campo", "ixachi", "akal")
    ok &= comprobar(f"[{modo}] filtro --campo (sin importar mayusculas)", rc == 0 and sorted({r['campo'] for r in f}) == ["AKAL", "IXACHI"] and len(f) == 5, f"filas={len(f)}")
rc, f, out = correr(f"{base}/pag/svc/FeatureServer/0", "--campo", "NO-EXISTE")
ok &= comprobar("campo inexistente termina con aviso, sin archivo roto", rc != 0 and "No se descargo ningun pozo" in out)
srv.shutdown()
print("\nTODO BIEN" if ok else "\nHAY FALLAS")
sys.exit(0 if ok else 1)
