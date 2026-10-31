"""Valida los sismos del CSV del USGS y produce un informe HTML estático."""

import csv
import math
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

BASE = Path(__file__).resolve().parent
NOMBRE_ESTUDIANTE = "Juan Pablo Vargas"  # Reemplazar antes de entregar.
REPOSITORIO_PREDETERMINADO = "JuanPabloVargasRodriguez/monitor-sismos-actions"
COLUMNAS_OBLIGATORIAS = {"time", "mag", "place", "id", "type"}
URL_USGS = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.csv"


def convertir_fecha(valor, numero_fila):
    try:
        fecha = datetime.fromisoformat(valor.strip().replace("Z", "+00:00"))
        if fecha.tzinfo is None:
            raise ValueError("la fecha no incluye zona horaria")
        return fecha.astimezone(timezone.utc)
    except (ValueError, AttributeError) as error:
        raise ValueError(f"Fila {numero_fila}: fecha inválida: {valor!r}") from error


def leer_sismos(ruta_csv):
    """Devuelve solo eventos earthquake con fecha UTC y magnitud numérica."""
    sismos = []
    with Path(ruta_csv).open("r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        columnas = set(lector.fieldnames or [])
        faltantes = COLUMNAS_OBLIGATORIAS - columnas
        if faltantes:
            raise ValueError(f"Faltan columnas obligatorias: {', '.join(sorted(faltantes))}")

        for numero_fila, fila in enumerate(lector, start=2):
            if (fila.get("type") or "").strip().lower() != "earthquake":
                continue

            identificador = (fila.get("id") or "").strip()
            ubicacion = (fila.get("place") or "").strip()
            magnitud_texto = (fila.get("mag") or "").strip()
            if not identificador or not ubicacion or not magnitud_texto:
                raise ValueError(f"Fila {numero_fila}: falta id, place o mag.")

            fecha_utc = convertir_fecha(fila.get("time") or "", numero_fila)
            try:
                magnitud = float(magnitud_texto)
            except ValueError as error:
                raise ValueError(f"Fila {numero_fila}: magnitud no numérica: {magnitud_texto!r}") from error
            if not math.isfinite(magnitud):
                raise ValueError(f"Fila {numero_fila}: magnitud no finita: {magnitud_texto!r}")

            sismos.append({"id": identificador, "fecha": fecha_utc,
                           "magnitud": magnitud, "ubicacion": ubicacion})

    if not sismos:
        raise ValueError("No hay eventos con type = earthquake en el CSV.")
    return sismos


def calcular_metricas(sismos):
    if not sismos:
        raise ValueError("No se pueden calcular indicadores sin sismos.")
    return {
        "cantidad": len(sismos),
        "magnitud_maxima": max(s["magnitud"] for s in sismos),
        "mas_reciente": max(s["fecha"] for s in sismos),
    }


def mostrar_fecha(fecha):
    return fecha.astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")


def generar_informe(sismos, fecha_descarga, ruta_salida, nombre=NOMBRE_ESTUDIANTE,
                    repositorio=None):
    """Crea un HTML autocontenido con indicadores, tabla, barras y enlaces."""
    if fecha_descarga.tzinfo is None:
        raise ValueError("La fecha de descarga debe incluir una zona horaria (UTC).")
    fecha_descarga = fecha_descarga.astimezone(timezone.utc)
    repo = repositorio or os.environ.get("GITHUB_REPOSITORY", REPOSITORIO_PREDETERMINADO)
    url_repo = f"https://github.com/{repo}"
    metricas = calcular_metricas(sismos)
    ultimos = sorted(sismos, key=lambda s: s["fecha"], reverse=True)[:10]
    por_fecha = Counter(s["fecha"].date().isoformat() for s in sismos)
    maximo = max(por_fecha.values())
    filas = "\n".join(
        f"<tr><td>{mostrar_fecha(s['fecha'])}</td>"
        f"<td>{escape(s['ubicacion'])}</td><td>{s['magnitud']:.2f}</td></tr>"
        for s in ultimos
    )
    barras = "\n".join(
        f'<div class="columna"><span class="total">{cantidad}</span>'
        f'<div class="barra" style="height:{max(4, cantidad/maximo*185):.1f}px" '
        f'role="img" aria-label="{fecha}: {cantidad} sismos"></div>'
        f'<span class="dia">{escape(fecha[5:])}</span></div>'
        for fecha, cantidad in sorted(por_fecha.items())
    )
    periodo_inicio = mostrar_fecha(fecha_descarga - timedelta(days=7))
    periodo_fin = mostrar_fecha(fecha_descarga)
    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Monitor automático de sismos recientes</title>
<style>
:root{{--fondo:#f3f6fb;--oscuro:#172640;--azul:#2763c5;--claro:#e5edfb;--borde:#dbe3f0}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--fondo);color:var(--oscuro);font-family:system-ui,-apple-system,Segoe UI,sans-serif}}
header{{background:linear-gradient(125deg,#122949,#215caa);color:#fff;padding:43px max(20px,calc((100vw - 1040px)/2))}}
header h1{{margin:0 0 8px;font-size:clamp(1.8rem,4vw,2.7rem)}}header p{{margin:6px 0;color:#dbe9ff}}
main{{max-width:1080px;margin:30px auto;padding:0 20px}}section{{background:#fff;border:1px solid var(--borde);border-radius:16px;padding:24px;margin:22px 0;box-shadow:0 4px 18px #1b32500c}}
h2{{margin:0 0 18px}}.sub{{color:#455a77;line-height:1.65}}.tarjetas{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}}
.tarjeta{{background:#fff;border:1px solid var(--borde);border-radius:14px;padding:20px}}.dato{{font-size:clamp(1.3rem,3vw,2.1rem);font-weight:750;color:var(--azul);margin-top:7px}}
.etiqueta{{font-size:.9rem;color:#586982}}.grafico{{display:flex;align-items:flex-end;gap:12px;min-height:225px;overflow-x:auto;border-bottom:1px solid #9caec7;padding:20px 5px 0}}
.columna{{min-width:50px;flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:6px}}.barra{{width:min(52px,90%);border-radius:6px 6px 0 0;background:linear-gradient(#4d96ef,#2763c5)}}
.total{{font-size:.8rem;font-weight:650}}.dia{{font-size:.75rem;color:#5c718d;white-space:nowrap;padding-bottom:9px}}
table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;padding:13px 10px;border-bottom:1px solid #e9eef6}}th{{background:#eef4ff}}.tabla{{overflow-x:auto}}a{{color:#2461b5}}header a{{color:#fff}}footer{{text-align:center;color:#5d718b;padding:0 18px 30px}}
@media(max-width:650px){{.tarjetas{{grid-template-columns:1fr}}section{{padding:18px}}}}
</style>
</head>
<body>
<header><h1>Monitor automático de sismos recientes</h1><p>Estudiante: {escape(nombre)}</p>
<p>Fuente: <a href="{URL_USGS}" target="_blank" rel="noopener">USGS — CSV, magnitud ≥ 2,5, últimos 7 días</a></p></header>
<main><section><h2>Información de la consulta</h2><p class="sub"><b>Descarga:</b> {mostrar_fecha(fecha_descarga)}<br>
<b>Periodo consultado (ventana móvil de siete días):</b> {periodo_inicio} a {periodo_fin}.<br>
<b>Eventos analizados:</b> únicamente registros de tipo <code>earthquake</code>.</p></section>
<div class="tarjetas"><div class="tarjeta"><div class="etiqueta">Cantidad de sismos</div><div class="dato">{metricas['cantidad']}</div></div>
<div class="tarjeta"><div class="etiqueta">Magnitud máxima</div><div class="dato">{metricas['magnitud_maxima']:.2f}</div></div>
<div class="tarjeta"><div class="etiqueta">Evento más reciente (UTC)</div><div class="dato" style="font-size:1.2rem">{mostrar_fecha(metricas['mas_reciente'])}</div></div></div>
<section><h2>Sismos por fecha (UTC)</h2><p class="sub">Cada barra representa el número de sismos registrados en esa fecha. No se suman magnitudes.</p>
<div class="grafico" aria-label="Gráfico de cantidad de sismos por fecha">{barras}</div></section>
<section><h2>Los 10 sismos más recientes</h2><div class="tabla"><table><thead><tr><th>Fecha y hora (UTC)</th><th>Ubicación</th><th>Magnitud</th></tr></thead>
<tbody>{filas}</tbody></table></div></section>
<section><h2>Proyecto y ejecución automática</h2><p>Consulta el <a href="{escape(url_repo, quote=True)}" target="_blank" rel="noopener">repositorio en GitHub</a> y el
<a href="{escape(url_repo + '/actions', quote=True)}" target="_blank" rel="noopener">historial de GitHub Actions</a>.</p></section></main>
<footer>Elaborado con Python y GitHub Actions · Datos públicos del USGS · Todos los horarios en UTC</footer>
</body></html>'''
    destino = Path(ruta_salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    return destino


def main():
    try:
        sismos = leer_sismos(BASE / "datos.csv")
        texto = (BASE / "fecha_descarga_utc.txt").read_text(encoding="utf-8").strip()
        fecha_descarga = datetime.fromisoformat(texto.replace("Z", "+00:00"))
        ruta = generar_informe(sismos, fecha_descarga, BASE / "public" / "index.html")
        print(f"Informe generado: {ruta}")
        print(f"Sismos validados: {len(sismos)}")
    except (OSError, ValueError) as error:
        raise SystemExit(f"ERROR al generar el informe: {error}") from error


if __name__ == "__main__":
    main()
