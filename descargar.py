"""Descarga el CSV oficial del USGS y registra cuándo terminó la descarga (UTC)."""

import csv
import io
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

URL_USGS = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.csv"
BASE = Path(__file__).resolve().parent
ARCHIVO_DATOS = BASE / "datos.csv"
ARCHIVO_FECHA = BASE / "fecha_descarga_utc.txt"
COLUMNAS = {"time", "mag", "place", "id", "type"}


def descargar():
    peticion = Request(URL_USGS, headers={"User-Agent": "monitor-sismos-actions/1.0"})
    try:
        with urlopen(peticion, timeout=45) as respuesta:
            contenido = respuesta.read()

        if not contenido:
            raise ValueError("El USGS devolvió un archivo vacío.")

        texto = contenido.decode("utf-8-sig")
        lector = csv.DictReader(io.StringIO(texto))
        columnas = set(lector.fieldnames or [])
        faltantes = COLUMNAS - columnas
        if faltantes:
            raise ValueError(f"El CSV descargado no contiene: {', '.join(sorted(faltantes))}")
        if next(lector, None) is None:
            raise ValueError("El CSV descargado no contiene registros.")

        # Reemplazo atómico: una descarga fallida no sobrescribe la última copia correcta.
        temporal = BASE / "datos.csv.tmp"
        temporal.write_bytes(contenido)
        os.replace(temporal, ARCHIVO_DATOS)
        fecha = datetime.now(timezone.utc).isoformat(timespec="seconds")
        ARCHIVO_FECHA.write_text(fecha, encoding="utf-8")
        print(f"Descarga correcta: {ARCHIVO_DATOS.name}")
        print(f"Fecha y hora de consulta: {fecha} (UTC)")
    except Exception as error:
        raise SystemExit(f"ERROR al descargar CSV del USGS: {error}") from error


if __name__ == "__main__":
    descargar()
