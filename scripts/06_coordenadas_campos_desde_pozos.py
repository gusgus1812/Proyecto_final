#!/usr/bin/env python3
"""
06_coordenadas_campos_desde_pozos.py
Calcula la ubicacion de cada campo a partir de las coordenadas de sus pozos y la guarda en
data/external/coordenadas_campos.csv (nombre,lat,lon,nota). Asi el mapa no depende de
coordenadas puestas a mano ni de la pagina: basta con los pozos que ya descargaste.

El punto de cada campo es la MEDIANA de latitud y longitud de sus pozos (la mediana no se
deja arrastrar por un pozo lejano o mal capturado). La nota indica con cuantos pozos se
calculo y la extension aproximada del campo en km.

Uso:
    python3 scripts/06_coordenadas_campos_desde_pozos.py
    python3 scripts/06_coordenadas_campos_desde_pozos.py --entrada data/external/pozos.csv --salida mis_campos.csv

Requiere haber corrido antes scripts/03_normalizar_pozos.py (genera data/external/pozos.csv).
Los pozos de demostracion (demo=1) se ignoran, salvo con --incluir-demo.
"""
import argparse
import csv
import math
import re
import statistics
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CAMPOS = RAIZ / "data" / "processed" / "campos_limpio.csv"
ENTRADA = RAIZ / "data" / "external" / "pozos.csv"
SALIDA = RAIZ / "data" / "external" / "coordenadas_campos.csv"


def clave(s):
    s = "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.upper().strip())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", type=Path, default=ENTRADA)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    ap.add_argument("--incluir-demo", action="store_true", help="incluye pozos ficticios (solo para pruebas)")
    a = ap.parse_args()

    if not a.entrada.exists():
        raise SystemExit(f"No existe {a.entrada}. Primero: python3 scripts/05_descargar_pozos_arcgis.py y "
                         "python3 scripts/03_normalizar_pozos.py data/external/pozos_arcgis_crudo.csv")
    with open(CAMPOS, encoding="utf-8-sig", newline="") as f:
        oficiales = {clave(r["nombre"]): r["nombre"] for r in csv.DictReader(f)}

    pts = {}
    ignorados = 0
    with open(a.entrada, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if not a.incluir_demo and str(r.get("demo", "")).strip() in ("1", "True", "true"):
                ignorados += 1
                continue
            try:
                lat, lon = float(r["lat"]), float(r["lon"])
            except (KeyError, ValueError):
                continue
            k = clave(r.get("campo", ""))
            if k in oficiales:
                pts.setdefault(oficiales[k], []).append((lat, lon))

    filas = []
    for nombre, p in pts.items():
        lat = statistics.median(x[0] for x in p)
        lon = statistics.median(x[1] for x in p)
        alto = (max(x[0] for x in p) - min(x[0] for x in p)) * 111
        ancho = (max(x[1] for x in p) - min(x[1] for x in p)) * 111 * math.cos(math.radians(lat))
        filas.append({"nombre": nombre, "lat": round(lat, 5), "lon": round(lon, 5),
                      "nota": f"mediana de {len(p)} pozos; extension ~{max(alto, ancho):.0f} km", "_n": len(p)})
    if not filas:
        raise SystemExit("Ningun pozo con coordenadas pertenece a los 477 campos"
                         + (f" ({ignorados} pozos de demostracion ignorados; usa --incluir-demo solo para probar)" if ignorados else "") + ".")
    filas.sort(key=lambda x: -x["_n"])
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    with open(a.salida, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["nombre", "lat", "lon", "nota"], extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    print(f"OK -> {a.salida}\n{len(filas)} de {len(oficiales)} campos con ubicacion calculada "
          f"({len(oficiales) - len(filas)} sin pozos con coordenadas)")
    print("Siguiente: python3 scripts/02_build_web.py")


if __name__ == "__main__":
    main()
