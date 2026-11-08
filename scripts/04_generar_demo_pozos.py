#!/usr/bin/env python3
"""
04_generar_demo_pozos.py
Genera data/demo/pozos_DEMO_ficticio.csv con pozos FICTICIOS (columna demo=1) que imitan
el esquema real del mapa de la CNH, solo para probar la interfaz. NO son pozos reales.

Uso:  python3 scripts/04_generar_demo_pozos.py
"""
import csv
import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "demo" / "pozos_DEMO_ficticio.csv"
random.seed(7)

# campo: (lat, lon, entidad, ubicacion, capa, tipo de hidrocarburo)  -- posiciones referenciales
BASE = {
    "IXACHI": (18.40, -95.90, "VERACRUZ DE IGNACIO DE LA LLAVE", "TERRESTRE", "Zona Veracruz", "GAS Y CONDENSADO"),
    "AKAL": (19.85, -92.05, "CAMPECHE", "MARINO", "Zona Aguas Someras", "ACEITE"),
    "MALOOB": (19.60, -92.20, "CAMPECHE", "MARINO", "Zona Aguas Someras", "ACEITE"),
    "AYATSIL": (19.70, -92.30, "CAMPECHE", "MARINO", "Zona Aguas Someras", "ACEITE"),
    "TRION": (24.60, -96.70, "TAMAULIPAS", "MARINO", "Zona Aguas Profundas", "ACEITE"),
    "ZAMA": (18.85, -93.50, "TABASCO", "MARINO", "Zona Aguas Someras", "ACEITE"),
    "QUESQUI": (17.90, -93.50, "TABASCO", "TERRESTRE", "Zona Sureste", "GAS Y CONDENSADO"),
}
ESTADOS = ["PRODUCTOR", "PRODUCTOR", "PRODUCTOR", "TAPONADO", "CERRADO", "ABANDONADO", "EN ESPERA", ""]
CLASES = ["DESARROLLO", "DESARROLLO", "EXPLORATORIO"]
TRAY = ["VERTICAL", "DIRECCIONAL", "HORIZONTAL"]
MES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

COLS = ["pozo", "campo", "entidad", "ubicacion", "clasificacion", "estado", "tipo_hidrocarburo", "fecha_inicio",
        "fecha_fin", "profundidad_total_m", "profundidad_vertical_m", "trayectoria", "disponible", "capa", "lat", "lon", "demo"]
filas = []
for campo, (la, lo, ent, ubic, capa, tipo) in BASE.items():
    for i in range(1, random.randint(9, 14)):
        anio, mes, dia = random.randint(1998, 2022), random.randint(0, 11), random.randint(1, 25)
        dur = random.randint(60, 400)
        fin_m, fin_a = (mes + dur // 30) % 12, anio + (mes + dur // 30) // 12
        total = random.randint(2500, 7200)
        filas.append({
            "pozo": f"DEMO-{campo[:3]}-{i:02d}", "campo": campo, "entidad": ent, "ubicacion": ubic,
            "clasificacion": random.choice(CLASES), "estado": random.choice(ESTADOS), "tipo_hidrocarburo": tipo if random.random() > .3 else "",
            "fecha_inicio": f"{dia:02d}-{MES[mes]}-{anio}", "fecha_fin": f"{min(dia + 5, 28):02d}-{MES[fin_m]}-{fin_a}",
            "profundidad_total_m": total, "profundidad_vertical_m": total - random.randint(0, 400),
            "trayectoria": random.choice(TRAY) if random.random() > .4 else "", "disponible": "DISPONIBLE", "capa": capa,
            "lat": round(la + random.uniform(-.08, .08), 5), "lon": round(lo + random.uniform(-.08, .08), 5), "demo": 1})

SALIDA.parent.mkdir(parents=True, exist_ok=True)
with open(SALIDA, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(filas)
print(f"OK -> {SALIDA} ({len(filas)} pozos ficticios)")
