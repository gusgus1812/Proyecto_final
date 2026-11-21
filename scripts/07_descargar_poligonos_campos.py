#!/usr/bin/env python3
# Autor: Emmanuel Vázquez Alfaro y Gustavo Angel Nava Bautista · © 2026 · Proyecto «Reservas de hidrocarburos de México». Ver LICENSE.

"""
07_descargar_poligonos_campos.py
Descarga las SUPERFICIES (poligonos) de los campos desde un servicio ArcGIS REST y las guarda en
data/external/campos_poligonos.geojson, ya aligeradas (coordenadas con 4 decimales y solo el nombre
del campo). 02_build_web.py las incrusta y el mapa las dibuja; al dar clic en una superficie se
abre la ficha del campo.

Solo usa la libreria estandar. Corre en TU computadora (el servidor de la CNH/SEMARNAT no es
accesible desde el entorno donde se desarrollo).

Uso:
    python scripts/07_descargar_poligonos_campos.py --buscar                 (lista capas candidatas)
    python scripts/07_descargar_poligonos_campos.py                          (busca y descarga la mejor)
    python scripts/07_descargar_poligonos_campos.py --url <URL_DE_LA_CAPA>   (capa concreta, termina en /0, /1...)

Como saber la URL de la capa: en el mapa de la CNH abre las herramientas del navegador (F12) ->
pestana Red/Network, enciende la capa de campos y busca una peticion que contenga "/FeatureServer/N/query"
o "/MapServer/N/query"; copia la URL hasta el numero de capa.
"""
import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "external" / "campos_poligonos.geojson"
RAICES = ["https://geomaticasig1.semarnat.gob.mx/arcgis/rest/services/Hosted"]
UA = {"User-Agent": "Mozilla/5.0 (proyecto-reservas)"}


def get(url, params=None, intentos=3, espera=90):
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    url = urllib.parse.quote(url, safe=":/?&=%,+")   # nombres de servicio con acentos o espacios
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=espera) as r:
                j = json.loads(r.read().decode("utf-8", "replace"))
            if isinstance(j, dict) and "error" in j:
                raise RuntimeError(j["error"])
            return j
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError, UnicodeError, OSError) as e:
            if i == intentos - 1:
                raise SystemExit(f"No pude leer {url[:150]}\n  {e}")
            time.sleep(1.5 * (i + 1))


def sin_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn")


def buscar_capas():
    """Recorre los servicios de las carpetas conocidas y devuelve capas de poligonos."""
    hallazgos = []
    for raiz in RAICES:
        try:
            catalogo = get(raiz, {"f": "json"})
        except SystemExit as e:
            print("  (sin acceso a", raiz, ")", file=sys.stderr)
            continue
        for s in catalogo.get("services", []):
            if s["type"] not in ("FeatureServer", "MapServer"):
                continue
            base = f"{raiz.rsplit('/services/', 1)[0]}/services/{s['name']}/{s['type']}"
            print("  revisando", s["name"], flush=True)
            try:
                info = get(base, {"f": "json"}, intentos=1, espera=15)
            except SystemExit:
                continue
            for c in info.get("layers", []):
                url = f"{base}/{c['id']}"
                hallazgos.append((s["name"], c["name"], url))
    out = []
    for srv, nombre, url in hallazgos:
        try:
            meta = get(url, {"f": "json"}, intentos=1, espera=15)
        except SystemExit:
            continue
        if meta.get("geometryType") == "esriGeometryPolygon":
            out.append((srv, nombre, url, meta))
    return out


def puntaje(srv, nombre):
    t = sin_acentos(f"{srv} {nombre}").lower()
    p = 0
    if "campo" in t:
        p += 3
    if "reserva" in t or "hidrocarb" in t:
        p += 1
    if "pozo" in t or "area" in t.split() and "contractual" in t:
        p -= 3
    return p


def anillos_a_geojson(rings):
    """Convierte anillos Esri a MultiPolygon (horario = exterior, antihorario = hueco)."""
    def area(r):
        return sum((r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1]) for i in range(len(r) - 1)) / 2
    polis = []
    for r in rings:
        if len(r) < 4:
            continue
        if area(r) < 0 or not polis:     # horario en Esri = exterior
            polis.append([r])
        else:
            polis[-1].append(r)
    return {"type": "MultiPolygon", "coordinates": polis}


def descargar(url, lote):
    meta = get(url, {"f": "json"})
    campos = [f["name"] for f in meta.get("fields", [])]
    clave_nombre = next((c for c in campos if sin_acentos(c).lower() in ("nombre", "campo", "name", "nombre_cam", "nom_campo")), None) \
        or next((c for c in campos if "nombre" in sin_acentos(c).lower()), None)
    if not clave_nombre:
        raise SystemExit(f"No encontre la columna con el nombre del campo. Columnas: {campos}")
    clave_sup = next((c for c in campos if "superf" in sin_acentos(c).lower()), None)
    ids = get(f"{url}/query", {"where": "1=1", "returnIdsOnly": "true", "f": "json"}).get("objectIds") or []
    print(f"Capa: {meta.get('name')} · {len(ids)} poligonos · columna nombre: {clave_nombre}")
    feats = []
    for i in range(0, len(ids), lote):
        grupo = ids[i:i + lote]
        j = get(f"{url}/query", {"objectIds": ",".join(map(str, grupo)), "outFields": "*", "outSR": 4326,
                                 "returnGeometry": "true", "geometryPrecision": 4, "maxAllowableOffset": 0.0008,
                                 "f": "json"})
        for f in j.get("features", []):
            g = f.get("geometry") or {}
            if not g.get("rings"):
                continue
            a = f["attributes"]
            nombre = str(a.get(clave_nombre) or "").strip()
            if not nombre:
                continue
            geo = anillos_a_geojson([[[round(x, 4), round(y, 4)] for x, y in r] for r in g["rings"]])
            props = {"nombre": nombre}
            if clave_sup and a.get(clave_sup) is not None:
                props["superficie_km2"] = a[clave_sup]
            feats.append({"type": "Feature", "properties": props, "geometry": geo})
        print(f"  {min(i + lote, len(ids))}/{len(ids)}")
    return feats


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", help="URL de la capa de poligonos (termina en /N)")
    ap.add_argument("--archivo", type=Path, help="GeoJSON local con los poligonos (por ejemplo convertido desde un shapefile)")
    ap.add_argument("--buscar", action="store_true", help="solo lista capas candidatas")
    ap.add_argument("--lote", type=int, default=50)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()

    if a.archivo:
        g = json.loads(a.archivo.read_text(encoding="utf-8-sig"))
        feats = []
        for f in g.get("features", []):
            pr = f.get("properties") or {}
            k = next((c for c in pr if sin_acentos(c).lower() in ("nombre", "campo", "name", "nom_campo", "nombre_cam")), None) \
                or next((c for c in pr if "nombre" in sin_acentos(c).lower()), None)
            if not k or not f.get("geometry") or not str(pr.get(k) or "").strip():
                continue
            redondea = lambda c: [round(c[0], 4), round(c[1], 4)] if isinstance(c[0], (int, float)) else [redondea(x) for x in c]
            geo = {"type": f["geometry"]["type"], "coordinates": redondea(f["geometry"]["coordinates"])}
            sup = next((pr[c] for c in pr if "superf" in sin_acentos(c).lower() and pr[c] is not None), None)
            props = {"nombre": str(pr[k]).strip(), **({"superficie_km2": sup} if sup is not None else {})}
            feats.append({"type": "Feature", "properties": props, "geometry": geo})
        if not feats:
            raise SystemExit("No encontre poligonos con una columna de nombre en ese archivo.")
        a.salida.parent.mkdir(parents=True, exist_ok=True)
        txt = json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":"))
        a.salida.write_text(txt, encoding="utf-8")
        print(f"OK -> {a.salida} ({len(txt) / 1024:.0f} KB, {len(feats)} superficies)\nSiguiente: python scripts/02_build_web.py")
        return

    url = a.url
    if not url or a.buscar:
        print("Buscando capas de poligonos...")
        cand = sorted(buscar_capas(), key=lambda x: -puntaje(x[0], x[1]))
        if not cand:
            raise SystemExit("No encontre capas de poligonos. Usa --url con la URL de la capa (ver --help).")
        for srv, nombre, u, meta in cand:
            print(f"  [{puntaje(srv, nombre):+d}] {srv} / {nombre}\n       {u}")
        if a.buscar:
            return
        url = cand[0][2]
        print("Usando la primera:", url)

    feats = descargar(url.rstrip("/"), a.lote)
    if not feats:
        raise SystemExit("La capa no devolvio poligonos.")
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":"))
    a.salida.write_text(txt, encoding="utf-8")
    print(f"OK -> {a.salida} ({len(txt) / 1024:.0f} KB, {len(feats)} superficies)")
    print("Siguiente: python scripts/02_build_web.py")


if __name__ == "__main__":
    main()
