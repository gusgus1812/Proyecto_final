#!/usr/bin/env python3
"""
03_normalizar_pozos.py
Lleva un CSV/XLSX de pozos al formato del dashboard y lo cruza con los 477 campos.
Entiende tanto los nombres de la ventana del mapa de la CNH (ESTADO ACTUAL, CLASIFICACIÓN,
PROFUNDIDAD TOTAL…) como los nombres crudos del servicio ArcGIS (estado_act, clasificac,
profundida…), que es lo que baja scripts/05_descargar_pozos_arcgis.py.

Uso:
    python3 scripts/03_normalizar_pozos.py data/external/pozos_arcgis_crudo.csv
    python3 scripts/03_normalizar_pozos.py mis_pozos.csv --autocorregir

Genera:
    data/external/pozos.csv                      (formato canonico; lo lee 02_build_web.py)
    data/processed/pozos_resumen.json            (conteos globales)
    data/processed/pozos_cobertura_campos.csv    (pozos de cada uno de los 477 campos)
    data/processed/pozos_sin_campo.csv           (pozos cuyo campo no coincide + sugerencia)
"""
import argparse
import difflib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CAMPOS = RAIZ / "data" / "processed" / "campos_limpio.csv"
SALIDA = RAIZ / "data" / "external" / "pozos.csv"
PROC = RAIZ / "data" / "processed"

# nombre canonico -> alias posibles (minusculas, sin acentos)
ALIAS = {
    "pozo": ["pozo", "nombre_pozo", "nombre del pozo", "well", "nombre"],
    "campo": ["campo", "field", "nombre_campo", "nombre del campo"],
    "entidad": ["entidad", "entidad federativa"],
    "ubicacion": ["ubicacion", "ubicacin"],
    "clasificacion": ["clasificacion", "clasificac", "tipo_pozo", "tipo de pozo", "objetivo"],
    "estado": ["estado actual", "estado_act", "estado", "estatus", "status", "estado_pozo", "estado del pozo", "situacion"],
    "tipo_hidrocarburo": ["tipo_hidrocarburo", "tipo de hidrocarburo", "tipo_de_hi", "fluido", "hidrocarburo"],
    "fecha_inicio": ["fecha_inicio", "fecha inicio perforacion", "fecha_inic", "fecha inicio"],
    "fecha_fin": ["fecha_fin", "fecha fin perforacion", "fecha_fin_", "fecha fin", "fecha_terminacion", "fecha"],
    "profundidad_total_m": ["profundidad_total_m", "profundidad total", "profundida", "profundidad", "prof"],
    "profundidad_vertical_m": ["profundidad_vertical_m", "profundidad vertical", "profundi_1"],
    "trayectoria": ["trayectoria", "trayectori"],
    "disponible": ["disponible"],
    "capa": ["capa", "pozos"],
    "lat": ["lat", "latitud", "latitude", "y"],
    "lon": ["lon", "lng", "longitud", "longitude", "x"],
    "demo": ["demo"],
}
CANON = list(ALIAS)
MESES = {"ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6, "JUL": 7, "AGO": 8, "SEP": 9, "SET": 9,
         "OCT": 10, "NOV": 11, "DIC": 12}


def sin_acentos(s):
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def clave(s):
    """Normaliza un nombre de campo para compararlo (mayusculas, sin acentos, espacios simples)."""
    return re.sub(r"\s+", " ", sin_acentos(s).upper().strip())


def clase_estado(txt):
    """Activo / Inactivo / Sin dato, a partir del texto del estado."""
    t = sin_acentos(txt).lower()
    if not t.strip():
        return "Sin dato"
    if re.search(r"inactiv|no product|cerrad|cierre|tapon|abandon|suspend|improduct|seco|sin produc|en espera|desmantel", t):
        return "Inactivo"
    if re.search(r"product|activ|operand|inyector|fluyente|bombeo|en operac", t):
        return "Activo"
    return "Sin dato"


def fecha_iso(v):
    """'01-AGO-2021', '2021-08-01', '01/08/2021' o milisegundos -> 'YYYY-MM-DD' (o vacio)."""
    v = str(v).strip()
    if not v or v.lower() == "nan":
        return ""
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", v)
    if m:
        return f"{m[1]}-{int(m[2]):02d}-{int(m[3]):02d}"
    m = re.match(r"^(\d{1,2})[-/ ]([A-Za-z]{3})[A-Za-z]*\.?[-/ ](\d{4})$", sin_acentos(v))
    if m and m[2].upper() in MESES:
        return f"{m[3]}-{MESES[m[2].upper()]:02d}-{int(m[1]):02d}"
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", v)
    if m:
        return f"{m[3]}-{int(m[2]):02d}-{int(m[1]):02d}"
    if re.fullmatch(r"\d{10,13}", v):
        return datetime.fromtimestamp(int(v) / (1000 if len(v) > 10 else 1), tz=timezone.utc).strftime("%Y-%m-%d")
    return ""


def leer(ruta):
    if ruta.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(ruta, dtype=str)
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(ruta, dtype=str, sep=None, engine="python", encoding=enc)
        except UnicodeDecodeError:
            continue
    raise SystemExit("No pude leer el archivo con utf-8 ni latin-1")


def numero(serie):
    return pd.to_numeric(serie.astype(str).str.replace(",", "", regex=False).str.strip(), errors="coerce")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", type=Path)
    ap.add_argument("--autocorregir", action="store_true",
                    help="reemplaza nombres de campo con una coincidencia muy parecida (>= 0.9)")
    a = ap.parse_args()

    campos = pd.read_csv(CAMPOS, encoding="utf-8-sig")
    por_clave = {clave(n): n for n in campos["nombre"]}

    df = leer(a.entrada)
    df.columns = [sin_acentos(c).strip().lower() for c in df.columns]
    ren, usados = {}, set()
    for canon, als in ALIAS.items():
        for al in als:
            if al in df.columns and al not in usados:
                ren[al] = canon
                usados.add(al)
                break
    df = df.rename(columns=ren)
    faltan = [c for c in ("pozo", "campo") if c not in df.columns]
    if faltan:
        raise SystemExit(f"Faltan columnas obligatorias {faltan}. Columnas halladas: {list(df.columns)}")
    for c in CANON:
        if c not in df.columns:
            df[c] = ""
    df = df[CANON].fillna("").astype(str).apply(lambda s: s.str.strip())
    df = df.replace({"nan": "", "None": "", "<NA>": ""})

    # --- campo
    df["campo"] = df["campo"].map(clave)
    sin = ~df["campo"].isin(por_clave)
    sugerencias = {}
    for n in df.loc[sin, "campo"].unique():
        m = difflib.get_close_matches(n, list(por_clave), n=1, cutoff=0.8)
        sugerencias[n] = (m[0] if m else "", difflib.SequenceMatcher(None, n, m[0]).ratio() if m else 0)
    if a.autocorregir:
        for n, (m, r) in sugerencias.items():
            if m and r >= 0.9:
                df.loc[df["campo"] == n, "campo"] = m
        sin = ~df["campo"].isin(por_clave)

    # --- estado, fechas, numeros, coordenadas
    df["estado_clase"] = df["estado"].map(clase_estado)
    for c in ("fecha_inicio", "fecha_fin"):
        df[c] = df[c].map(fecha_iso)
    for c in ("lat", "lon", "profundidad_total_m", "profundidad_vertical_m"):
        df[c] = numero(df[c])
    fuera = (df["lat"].notna() & ~df["lat"].between(14, 33.5)) | (df["lon"].notna() & ~df["lon"].between(-120, -84))
    df.loc[fuera, ["lat", "lon"]] = pd.NA  # coordenadas imposibles para Mexico
    df = df.drop_duplicates(subset=["pozo", "campo"])
    sin = ~df["campo"].isin(por_clave)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    df[CANON].to_csv(SALIDA, index=False, encoding="utf-8-sig")

    # --- cobertura por campo
    g = df.groupby("campo")["estado_clase"].value_counts().unstack(fill_value=0)
    for c in ("Activo", "Inactivo", "Sin dato"):
        if c not in g:
            g[c] = 0
    cob = pd.DataFrame({"nombre": campos["nombre"]})
    cob["clave"] = cob["nombre"].map(clave)
    cob = cob.merge(g[["Activo", "Inactivo", "Sin dato"]], left_on="clave", right_index=True, how="left").fillna(0)
    cob["n_pozos"] = cob[["Activo", "Inactivo", "Sin dato"]].sum(axis=1)
    cob = cob.drop(columns="clave").rename(columns={"Activo": "activos", "Inactivo": "inactivos", "Sin dato": "sin_dato"})
    cob.to_csv(PROC / "pozos_cobertura_campos.csv", index=False, encoding="utf-8-sig")

    huerf = df[sin].copy()
    huerf["sugerencia"] = huerf["campo"].map(lambda n: sugerencias.get(n, ("", 0))[0])
    huerf["similitud"] = huerf["campo"].map(lambda n: round(sugerencias.get(n, ("", 0))[1], 2))
    huerf[["pozo", "campo", "sugerencia", "similitud"]].to_csv(PROC / "pozos_sin_campo.csv", index=False, encoding="utf-8-sig")

    resumen = {
        "pozos": int(len(df)),
        "campos_con_pozos": int((cob["n_pozos"] > 0).sum()),
        "campos_total": int(len(campos)),
        "por_estado": df["estado_clase"].value_counts().to_dict(),
        "estados_texto_original": df["estado"].replace("", "(vacio)").value_counts().head(15).to_dict(),
        "pozos_sin_campo_reconocido": int(sin.sum()),
        "coordenadas_descartadas": int(fuera.sum()),
        "sin_coordenadas": int(df["lat"].isna().sum()),
        "sin_fecha_inicio": int((df["fecha_inicio"] == "").sum()),
    }
    (PROC / "pozos_resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    print(f"-> {SALIDA}\nSiguiente paso: python3 scripts/02_build_web.py")
    if sin.any():
        print(f"AVISO: {int(sin.sum())} pozos con campo vacio o que no coincide con los 477; "
              "revisa data/processed/pozos_sin_campo.csv (normal: el mapa incluye campos sin reservas)")


if __name__ == "__main__":
    main()
