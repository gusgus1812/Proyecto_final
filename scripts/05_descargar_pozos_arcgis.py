#!/usr/bin/env python3
"""
05_descargar_pozos_arcgis.py
Descarga los pozos desde un servicio ArcGIS REST (el tipo de servicio que usa el
Mapa de Hidrocarburos de la CNH) y los guarda como CSV con coordenadas.

Por defecto usa la capa publica "Pozos, 2024" (datos de la CNH / CNIH alojados en
SEMARNAT) cuyos campos coinciden con la ventana emergente del mapa:
pozo, campo, entidad, ubicacin, clasificac, estado_act, tipo_de_hi, fecha_inic,
fecha_fin_, profundida, profundi_1, trayectori, disponible y pozos (la zona/capa).

Uso:
    python3 scripts/05_descargar_pozos_arcgis.py
    python3 scripts/05_descargar_pozos_arcgis.py --campo IXACHI
    python3 scripts/05_descargar_pozos_arcgis.py --campo IXACHI AKAL TRION
    python3 scripts/05_descargar_pozos_arcgis.py URL_DE_LA_CAPA_O_DEL_SERVICIO [URL2 ...]

Siguiente paso:
    python3 scripts/03_normalizar_pozos.py data/external/pozos_arcgis_crudo.csv
    python3 scripts/02_build_web.py

Necesita internet. Solo usa la libreria estandar de Python.
Si el servicio cambia de direccion: abre el mapa, F12 > pestana Red, haz clic en un pozo y
busca la peticion que termina en /FeatureServer/<n>/query o /MapServer/<n>/query;
la URL hasta <n> es la que se pasa a este script.
"""
import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
URL_DEFECTO = "https://geomaticasig1.semarnat.gob.mx/arcgis/rest/services/Hosted/Pozos_2024/FeatureServer/0"
SALIDA = RAIZ / "data" / "external" / "pozos_arcgis_crudo.csv"
CABECERAS = {"User-Agent": "reservas-hidrocarburos/1.0 (proyecto academico)"}


def pedir(url, params=None, post=False, reintentos=4):
    """Hace una peticion a ArcGIS REST y devuelve el JSON; reintenta si falla."""
    params = dict(params or {})
    params.setdefault("f", "json")
    datos = urllib.parse.urlencode(params)
    for i in range(reintentos):
        try:
            if post:
                req = urllib.request.Request(url, data=datos.encode(), headers=CABECERAS)
            else:
                req = urllib.request.Request(url + "?" + datos, headers=CABECERAS)
            with urllib.request.urlopen(req, timeout=90) as r:
                js = json.loads(r.read().decode("utf-8"))
            if isinstance(js, dict) and "error" in js:
                raise RuntimeError(js["error"])
            return js
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError, RuntimeError) as e:
            if i == reintentos - 1:
                raise SystemExit(f"No se pudo leer {url}: {e}")
            time.sleep(2 ** i)


def capas_de(url):
    """Si la URL termina en un numero es una capa; si no, lista las capas del servicio."""
    url = url.rstrip("/")
    if url.rsplit("/", 1)[-1].isdigit():
        return [url]
    js = pedir(url)
    capas = [f"{url}/{c['id']}" for c in js.get("layers", [])]
    if not capas:
        raise SystemExit(f"El servicio {url} no devolvio capas")
    return capas


def fecha_iso(ms):
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError, OverflowError):
        return ""


def sql_texto(s):
    return "'" + s.replace("'", "''") + "'"


def descargar_capa(capa, meta, where, lote):
    campos = meta.get("fields", [])
    oid = next((c["name"] for c in campos if c.get("type") == "esriFieldTypeOID"), "objectid")
    maxrec = max(1, min(int(meta.get("maxRecordCount") or 1000), lote))
    base = {"where": where, "outFields": "*", "returnGeometry": "true", "outSR": "4326"}
    pagina = bool((meta.get("advancedQueryCapabilities") or {}).get("supportsPagination"))
    feats = []
    if pagina:
        desde = 0
        while True:
            js = pedir(capa + "/query", {**base, "orderByFields": oid, "resultOffset": desde,
                                         "resultRecordCount": maxrec}, post=True)
            lote_f = js.get("features", [])
            feats += lote_f
            print(f"   {len(feats)} pozos…", end="\r", flush=True)
            if not lote_f or not (js.get("exceededTransferLimit") or len(lote_f) >= maxrec):
                break
            desde += len(lote_f)
    else:  # servidores sin paginacion: se piden los ids y luego por lotes
        ids = sorted(pedir(capa + "/query", {"where": where, "returnIdsOnly": "true"}, post=True).get("objectIds") or [])
        for i in range(0, len(ids), maxrec):
            js = pedir(capa + "/query", {**base, "where": "1=1",
                                         "objectIds": ",".join(map(str, ids[i:i + maxrec]))}, post=True)
            feats += js.get("features", [])
            print(f"   {len(feats)} pozos…", end="\r", flush=True)
    print(" " * 40, end="\r")
    tipos_fecha = {c["name"] for c in campos if c.get("type") == "esriFieldTypeDate"}
    filas = []
    for f in feats:
        fila = {k.lower(): ("" if v is None else v) for k, v in (f.get("attributes") or {}).items()}
        for k in tipos_fecha:
            if fila.get(k.lower()) not in ("", None):
                fila[k.lower()] = fecha_iso(fila[k.lower()])
        g = f.get("geometry") or {}
        fila["lon"] = g.get("x", "")
        fila["lat"] = g.get("y", "")
        filas.append(fila)
    return filas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", nargs="*", default=[URL_DEFECTO], help="capa o servicio ArcGIS (por defecto, Pozos 2024)")
    ap.add_argument("--campo", nargs="+", help="solo pozos de estos campos (ej. --campo IXACHI AKAL)")
    ap.add_argument("--where", help="filtro SQL propio (si se da, se ignora --campo)")
    ap.add_argument("--lote", type=int, default=2000, help="maximo de pozos por peticion")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()

    todas = []
    for url in a.urls:
        for capa in capas_de(url):
            meta = pedir(capa)
            nombres = [c["name"].lower() for c in meta.get("fields", [])]
            if meta.get("geometryType") != "esriGeometryPoint" or "pozo" not in nombres:
                print(f"- {capa}: se omite (no es una capa de puntos con campo 'pozo')")
                continue
            where = a.where or "1=1"
            if not a.where and a.campo:
                col = next(c["name"] for c in meta["fields"] if c["name"].lower() == "campo") if "campo" in nombres else None
                if not col:
                    print(f"- {capa}: se omite (no tiene columna 'campo')")
                    continue
                where = f"UPPER({col}) IN ({', '.join(sql_texto(c.upper()) for c in a.campo)})"
            print(f"- {capa}  «{meta.get('name', '')}»  (max {meta.get('maxRecordCount')} por peticion)")
            filas = descargar_capa(capa, meta, where, a.lote)
            print(f"   {len(filas)} pozos descargados")
            todas += filas

    if not todas:
        raise SystemExit("No se descargo ningun pozo. Revisa la URL, el filtro o tu conexion.")
    cols = []
    for f in todas:
        for k in f:
            if k not in cols:
                cols.append(k)
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    with open(a.salida, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(todas)

    est = next((k for k in ("estado_act", "estado actual", "estado") if k in cols), None)
    print(f"\nOK -> {a.salida}  ({len(todas)} pozos, {sum(1 for f in todas if f.get('lat') in ('', None))} sin coordenadas)")
    if est:
        print("Estados:", dict(Counter(str(f.get(est, '')) or '(vacio)' for f in todas).most_common(8)))
    if "campo" in cols:
        print("Campos con mas pozos:", Counter(str(f.get('campo', '')) for f in todas).most_common(5))
    print("Siguiente: python3 scripts/03_normalizar_pozos.py", a.salida.relative_to(RAIZ) if a.salida.is_relative_to(RAIZ) else a.salida)


if __name__ == "__main__":
    sys.exit(main())
