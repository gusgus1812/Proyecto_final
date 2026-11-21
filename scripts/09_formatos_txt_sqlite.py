#!/usr/bin/env python3
# Autor: Emmanuel Vázquez Alfaro y Gustavo Angel Nava Bautista · © 2026 · Proyecto «Reservas de hidrocarburos de México». Ver LICENSE.
"""
09_formatos_txt_sqlite.py
Convierte los datos del proyecto entre CSV, TXT (separado por tabuladores, | o ;) y SQLite.
Solo usa la libreria estandar (csv, sqlite3).

Uso:
    python scripts/09_formatos_txt_sqlite.py exportar
        Lee data/processed/campos_limpio.csv y data/external/pozos.csv (si existe) y crea en data/export/:
        campos.txt, pozos.txt (tabuladores) y reservas.db (SQLite con las tablas campos y pozos).

    python scripts/09_formatos_txt_sqlite.py importar --db data/export/reservas.db
        Lee la tabla pozos de la base y escribe data/external/pozos.csv (el formato que usa 02_build_web.py).

    python scripts/09_formatos_txt_sqlite.py importar --txt mis_pozos.txt
        Lee un TXT con separador (se detecta solo) y escribe data/external/pozos.csv.

    python scripts/09_formatos_txt_sqlite.py consulta "SELECT ubicacion, COUNT(*) FROM campos GROUP BY 1"
        Ejecuta una consulta SQL sobre data/export/reservas.db y muestra el resultado.
Despues: python scripts/02_build_web.py
"""
import argparse
import csv
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CAMPOS = RAIZ / "data" / "processed" / "campos_limpio.csv"
POZOS = RAIZ / "data" / "external" / "pozos.csv"
EXPORT = RAIZ / "data" / "export"
DB = EXPORT / "reservas.db"


def detectar(path):
    """Devuelve el separador mas probable en la primera linea del archivo."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        primera = f.readline()
    cuentas = {d: primera.count(d) for d in [",", "\t", "|", ";"]}
    d = max(cuentas, key=cuentas.get)
    return d if cuentas[d] else ","


def leer(path, sep=None):
    sep = sep or detectar(path)
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f, delimiter=sep)
        filas = [x for x in r if any(c.strip() for c in x)]
    if not filas:
        raise SystemExit(f"El archivo {path} esta vacio.")
    cab = [c.strip() for c in filas[0]]
    return cab, [dict(zip(cab, (c.strip() for c in x))) for x in filas[1:]]


def escribir(path, cab, filas, sep):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=sep, lineterminator="\n")
        w.writerow(cab)
        for r in filas:
            w.writerow([r.get(c, "") for c in cab])


def a_sqlite(con, tabla, cab, filas):
    cols = ", ".join(f'"{c}" TEXT' for c in cab)
    con.execute(f'DROP TABLE IF EXISTS "{tabla}"')
    con.execute(f'CREATE TABLE "{tabla}" ({cols})')
    con.executemany(f'INSERT INTO "{tabla}" VALUES ({",".join("?" * len(cab))})',
                    [[r.get(c, "") for c in cab] for r in filas])


def exportar():
    if not CAMPOS.exists():
        raise SystemExit(f"Falta {CAMPOS}. Corre antes: python scripts/01_limpieza_analisis.py")
    EXPORT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    resumen = []
    for nombre, ruta in [("campos", CAMPOS), ("pozos", POZOS)]:
        if not ruta.exists():
            print(f"  (sin {ruta.name}: se omite la tabla {nombre})")
            continue
        cab, filas = leer(ruta)
        escribir(EXPORT / f"{nombre}.txt", cab, filas, "\t")
        a_sqlite(con, nombre, cab, filas)
        resumen.append(f"{nombre}: {len(filas)} filas, {len(cab)} columnas")
    con.commit()
    con.close()
    print("OK -> data/export/ (campos.txt, pozos.txt, reservas.db)")
    for r in resumen:
        print("  ", r)


def importar(a):
    if a.db:
        con = sqlite3.connect(a.db)
        try:
            cur = con.execute('SELECT * FROM "pozos"')
        except sqlite3.OperationalError:
            raise SystemExit("La base no tiene la tabla 'pozos'.")
        cab = [d[0] for d in cur.description]
        filas = [dict(zip(cab, ["" if v is None else str(v) for v in r])) for r in cur]
        con.close()
        origen = a.db
    elif a.txt:
        cab, filas = leer(Path(a.txt))
        origen = a.txt
    else:
        raise SystemExit("Indica --db archivo.db o --txt archivo.txt")
    escribir(POZOS, cab, filas, ",")
    print(f"OK -> {POZOS} ({len(filas)} pozos, desde {origen})\nSiguiente: python scripts/02_build_web.py")


def consulta(sql):
    if not DB.exists():
        raise SystemExit("Primero corre: python scripts/09_formatos_txt_sqlite.py exportar")
    con = sqlite3.connect(DB)
    try:
        cur = con.execute(sql)
    except sqlite3.Error as e:
        raise SystemExit(f"Error SQL: {e}")
    print(" | ".join(d[0] for d in cur.description))
    for r in cur.fetchmany(50):
        print(" | ".join(str(v) for v in r))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("exportar")
    i = sp.add_parser("importar")
    i.add_argument("--db")
    i.add_argument("--txt")
    c = sp.add_parser("consulta")
    c.add_argument("sql")
    a = ap.parse_args()
    if a.cmd == "exportar":
        exportar()
    elif a.cmd == "importar":
        importar(a)
    else:
        consulta(a.sql)


if __name__ == "__main__":
    main()
