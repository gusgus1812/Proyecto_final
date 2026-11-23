#!/usr/bin/env python3
"""
Pruebas de scripts/03_normalizar_pozos.py.
- Funciones puras: nombres de campo, estado del pozo (activo/inactivo), fechas y numeros.
- Prueba completa con una tabla minima armada aqui mismo, en una carpeta temporal: no toca los
  archivos reales del proyecto ni forma parte del conjunto de datos.

Uso:  python tests/test_03_normalizar_pozos.py
"""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent


def cargar(nombre_archivo):
    """Importa un script cuyo nombre empieza con numero (no se puede con 'import')."""
    ruta = RAIZ / "scripts" / nombre_archivo
    spec = importlib.util.spec_from_file_location(ruta.stem, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


n03 = cargar("03_normalizar_pozos.py")


class TestFuncionesPuras(unittest.TestCase):
    def test_clave_normaliza_nombres_de_campo(self):
        self.assertEqual(n03.clave("  Ixachí   norte "), "IXACHI NORTE")

    def test_clase_estado(self):
        casos = {
            "PRODUCTOR": "Activo",
            "OPERANDO": "Activo",
            "INYECTOR PARA RECUPERACION SECUNDARIA O MEJORADA": "Activo",
            "CERRADO": "Inactivo",
            "TAPONAMIENTO PERMANENTE": "Inactivo",
            "ESPERANDO ABANDONO": "Inactivo",
            "CERRADO ESPERANDO INSTALACIONES DE PRODUCCION": "Inactivo",  # 'cerrado' pesa mas que 'produccion'
            "EN CONSTRUCCION": "Sin dato",
            "": "Sin dato",
        }
        for texto, esperado in casos.items():
            with self.subTest(texto):
                self.assertEqual(n03.clase_estado(texto), esperado)

    def test_fecha_iso(self):
        casos = {
            "25-MAY-1949": "1949-05-25",
            "01-AGO-2021": "2021-08-01",
            "2021-08-01": "2021-08-01",
            "01/08/2021": "2021-08-01",
            "1627776000000": "2021-08-01",  # milisegundos
            "": "",
            "nan": "",
            "no es fecha": "",
        }
        for texto, esperado in casos.items():
            with self.subTest(texto):
                self.assertEqual(n03.fecha_iso(texto), esperado)

    def test_numero_quita_comas_y_marca_invalidos_como_nulos(self):
        r = n03.numero(pd.Series(["1,038.2", " 7 ", "abc"]))
        self.assertEqual(r.iloc[0], 1038.2)
        self.assertEqual(r.iloc[1], 7)
        self.assertTrue(pd.isna(r.iloc[2]))


class TestNormalizacionCompleta(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        campo = pd.read_csv(n03.CAMPOS, encoding="utf-8-sig")["nombre"].iloc[0]  # un campo real
        cols = ["pozo", "campo", "estado_act", "fecha_inic", "profundida", "lat", "lon"]
        filas = [
            ["A-1", campo, "PRODUCTOR", "25-MAY-1949", "1038.2", "21.37", "-97.64"],
            ["A-1", campo, "PRODUCTOR", "25-MAY-1949", "1038.2", "21.37", "-97.64"],  # duplicado exacto
            ["B-2", campo, "CERRADO", "01-FEB-1922", "2500", "22.07", "-98.12"],
            ["B-2", campo, "TAPONAMIENTO PERMANENTE", "25-AGO-1966", "2601", "25.74", "-97.88"],  # mismo nombre y campo, otro pozo
            ["C-3", campo, "", "", "900", "99", "-97"],  # latitud imposible para Mexico
            ["D-4", "CAMPO QUE NO EXISTE", "OPERANDO", "2001-01-01", "1500", "20", "-100"],
        ]
        entrada = d / "entrada.csv"
        pd.DataFrame(filas, columns=cols).to_csv(entrada, index=False)
        for parche in (mock.patch.object(n03, "SALIDA", d / "pozos.csv"),
                       mock.patch.object(n03, "PROC", d),
                       mock.patch.object(sys, "argv", ["03", str(entrada)])):
            parche.start()
            self.addCleanup(parche.stop)
        with contextlib.redirect_stdout(io.StringIO()):
            n03.main()
        self.pozos = pd.read_csv(d / "pozos.csv", encoding="utf-8-sig")
        self.resumen = json.loads((d / "pozos_resumen.json").read_text(encoding="utf-8"))
        self.sin_campo = pd.read_csv(d / "pozos_sin_campo.csv", encoding="utf-8-sig")

    def test_solo_se_quitan_duplicados_exactos(self):
        self.assertEqual(self.resumen["filas_entrada"], 6)
        self.assertEqual(self.resumen["duplicados_exactos_eliminados"], 1)
        self.assertEqual(len(self.pozos), 5)

    def test_pozos_con_mismo_nombre_y_campo_pero_distintos_se_conservan(self):
        self.assertEqual((self.pozos["pozo"] == "B-2").sum(), 2)

    def test_coordenadas_imposibles_se_descartan(self):
        c3 = self.pozos[self.pozos["pozo"] == "C-3"].iloc[0]
        self.assertTrue(pd.isna(c3["lat"]) and pd.isna(c3["lon"]))
        self.assertEqual(self.resumen["coordenadas_descartadas"], 1)

    def test_clasificacion_activo_inactivo(self):
        self.assertEqual(self.resumen["por_estado"], {"Activo": 2, "Inactivo": 2, "Sin dato": 1})

    def test_fechas_quedan_en_formato_iso(self):
        a1 = self.pozos[self.pozos["pozo"] == "A-1"].iloc[0]
        self.assertEqual(a1["fecha_inicio"], "1949-05-25")

    def test_campo_inexistente_se_reporta_aparte(self):
        self.assertEqual(self.resumen["pozos_sin_campo_reconocido"], 1)
        self.assertEqual(list(self.sin_campo["pozo"]), ["D-4"])

    def test_salida_sin_columna_demo_y_con_16_columnas(self):
        self.assertNotIn("demo", self.pozos.columns)
        self.assertEqual(self.pozos.shape[1], 16)


if __name__ == "__main__":
    unittest.main(verbosity=2)