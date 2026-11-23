#!/usr/bin/env python3
"""
Pruebas de calidad de los datos que produce scripts/01_limpieza_analisis.py.
Comparan el archivo limpio (data/processed/campos_limpio.csv) con el original (data/raw/...).

Uso:  python scripts/01_limpieza_analisis.py      (genera el archivo limpio)
      python tests/test_01_limpieza.py
"""
import unittest
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data" / "raw" / "Campos_Reservas_01-01-2024.csv"
LIMPIO = RAIZ / "data" / "processed" / "campos_limpio.csv"


class TestLimpiezaReservas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = pd.read_csv(RAW, encoding="utf-8-sig")
        cls.df = pd.read_csv(LIMPIO, encoding="utf-8-sig")

    def test_original_tiene_477_campos_y_22_columnas(self):
        self.assertEqual(self.raw.shape, (477, 22))

    def test_limpio_conserva_los_477_campos(self):
        self.assertEqual(len(self.df), 477)

    def test_no_hay_nombres_duplicados(self):
        self.assertTrue(self.df["nombre"].is_unique)

    def test_nombres_en_mayusculas_y_sin_espacios_sobrantes(self):
        self.assertTrue((self.df["nombre"] == self.df["nombre"].str.strip().str.upper()).all())

    def test_ubicaciones_validas(self):
        self.assertEqual(set(self.df["ubicacion"]), {"Terrestre", "Marino", "Aguas someras"})

    def test_reservas_coherentes_1p_2p_3p(self):
        tol = 1e-9
        self.assertTrue((self.df["pce_1p"] <= self.df["pce_2p"] + tol).all(), "hay campos con 1P > 2P")
        self.assertTrue((self.df["pce_2p"] <= self.df["pce_3p"] + tol).all(), "hay campos con 2P > 3P")

    def test_superficie_cero_se_trata_como_sin_dato(self):
        sin = self.df["sin_superficie"]
        self.assertTrue(self.df.loc[sin, "superficie_km2"].isna().all())
        self.assertTrue((self.df.loc[~sin, "superficie_km2"] > 0).all())

    def test_certeza_esta_entre_0_y_1(self):
        c = self.df["certeza_1p_3p"].dropna()
        self.assertTrue(((c >= 0) & (c <= 1)).all())

    def test_probables_y_posibles_no_son_negativos(self):
        self.assertTrue((self.df["probables"] >= 0).all())
        self.assertTrue((self.df["posibles"] >= 0).all())

    def test_la_limpieza_no_altera_las_reservas(self):
        # columnas 4, 10 y 16 del original = petroleo crudo equivalente 1P, 2P y 3P
        for pos, col in ((4, "pce_1p"), (10, "pce_2p"), (16, "pce_3p")):
            with self.subTest(col):
                self.assertAlmostEqual(self.raw.iloc[:, pos].sum(), self.df[col].sum(), places=2)

    def test_totales_conocidos(self):
        self.assertEqual(round(self.df["pce_1p"].sum()), 8359)
        self.assertEqual(round(self.df["pce_2p"].sum()), 15497)
        self.assertEqual(round(self.df["pce_3p"].sum()), 23089)


if __name__ == "__main__":
    unittest.main(verbosity=2)