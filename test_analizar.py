"""Pruebas unitarias sin conexión a internet."""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from analizar import calcular_metricas, generar_informe, leer_sismos

ENCABEZADO = "time,mag,place,id,type\n"
FILA_1 = "2026-10-30T10:00:00.000Z,3.2,Región A,abc,earthquake\n"
FILA_2 = "2026-10-31T09:00:00.000Z,4.1,Región B,def,earthquake\n"


class TestMonitorSismos(unittest.TestCase):
    def guardar_csv(self, carpeta, contenido):
        ruta = Path(carpeta) / "ejemplo.csv"
        ruta.write_text(contenido, encoding="utf-8")
        return ruta

    def test_calculo_conocido(self):
        with tempfile.TemporaryDirectory() as carpeta:
            sismos = leer_sismos(self.guardar_csv(carpeta, ENCABEZADO + FILA_1 + FILA_2))
            metricas = calcular_metricas(sismos)
            self.assertEqual(metricas["cantidad"], 2)
            self.assertEqual(metricas["magnitud_maxima"], 4.1)
            self.assertEqual(metricas["mas_reciente"].day, 31)

    def test_rechaza_magnitud_invalida(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = self.guardar_csv(carpeta,
                ENCABEZADO + "2026-10-30T10:00:00Z,no-es-numero,Región A,x,earthquake\n")
            with self.assertRaisesRegex(ValueError, "magnitud no numérica"):
                leer_sismos(ruta)

    def test_detecta_columna_ausente(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = self.guardar_csv(carpeta, "time,mag,place,id\n"
                "2026-10-30T10:00:00Z,3.2,Región A,x\n")
            with self.assertRaisesRegex(ValueError, "Faltan columnas obligatorias: type"):
                leer_sismos(ruta)

    def test_genera_informe_html(self):
        with tempfile.TemporaryDirectory() as carpeta:
            sismos = leer_sismos(self.guardar_csv(carpeta, ENCABEZADO + FILA_1 + FILA_2))
            salida = Path(carpeta) / "public" / "index.html"
            generar_informe(sismos, datetime(2026, 10, 31, 12, tzinfo=timezone.utc),
                            salida, nombre="Estudiante de prueba",
                            repositorio="cuenta-ejemplo/monitor-sismos-actions")
            contenido = salida.read_text(encoding="utf-8")
            self.assertTrue(salida.exists())
            self.assertIn("Estudiante de prueba", contenido)
            self.assertIn("Región B", contenido)
            self.assertIn("12:00:00 UTC", contenido)
            self.assertIn("/actions", contenido)

    def test_ignora_otros_tipos(self):
        with tempfile.TemporaryDirectory() as carpeta:
            contenido = (ENCABEZADO + FILA_1 +
                         "2026-10-31T09:00:00Z,,Volcán,x,quarry blast\n")
            sismos = leer_sismos(self.guardar_csv(carpeta, contenido))
            self.assertEqual(len(sismos), 1)

    def test_rechaza_fecha_invalida(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = self.guardar_csv(carpeta, ENCABEZADO +
                "fecha-falsa,3.2,Región A,x,earthquake\n")
            with self.assertRaisesRegex(ValueError, "fecha inválida"):
                leer_sismos(ruta)


if __name__ == "__main__":
    unittest.main()
