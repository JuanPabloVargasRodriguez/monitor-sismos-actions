# Monitor automático de sismos recientes con GitHub Actions

Este proyecto descarga los sismos de magnitud 2,5+ registrados por el [USGS en los últimos 7 días](https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.csv), valida el CSV y construye una página HTML estática. La publicación se realiza con GitHub Actions y GitHub Pages.

## Personalizar antes de publicar

- En `analizar.py` cambia `NOMBRE_ESTUDIANTE = "TU NOMBRE COMPLETO"`.
- En `analizar.py` cambia `TU_USUARIO_GITHUB` por tu nombre de usuario de GitHub para que los enlaces funcionen también en local. En Actions se detecta automáticamente el repositorio.
- El repositorio debe llamarse `monitor-sismos-actions` y ser público.

## Comprobar el proyecto en Windows (terminal de VS Code)

```powershell
py --version
py -m unittest discover -v
py descargar.py
py analizar.py
```

Si no reconoce `py`, usa `python` en cada comando. Abre `public/index.html` en tu navegador.

Las pruebas son totalmente independientes de Internet. La descarga, en cambio, requiere Internet.

## Configurar GitHub Pages

En el repositorio: **Settings → Pages → Build and deployment → Source: GitHub Actions**.

El archivo `.github/workflows/sismos.yml` ejecuta dos trabajos: `ci` (pruebas, descarga, análisis, subida del artefacto) y `cd` (publicación con GitHub Pages). CD solo corre si CI fue correcto (`needs: ci`).

La automatización se activa con cambios en `main`, manualmente en **Actions → Monitor de sismos - CI/CD → Run workflow**, y cada seis horas (UTC) al minuto 17 con `17 */6 * * *`.

## Demostraciones solicitadas por la práctica

1. **Actualización de datos:** ejecutar `Run workflow` sin editar ni hacer commits y comprobar que la hora de descarga UTC cambia.
2. **Cambio de código:** modificar el título visible en `analizar.py`, ejecutar las pruebas localmente, hacer Commit + Push y verificar CI + CD exitosos y el nuevo título publicado.
3. **Fallo controlado:** cambiar temporalmente el valor esperado en `test_calculo_conocido`, por ejemplo `self.assertEqual(metricas["cantidad"], 999)`, hacer Commit + Push y confirmar CI en rojo, CD omitido y web anterior intacta. Restaurar `2`, hacer Commit + Push y confirmar CI + CD verdes.

## Entregables

- `https://TU_USUARIO_GITHUB.github.io/monitor-sismos-actions/`
- `https://github.com/TU_USUARIO_GITHUB/monitor-sismos-actions`

> `datos.csv`, `fecha_descarga_utc.txt` y `public/` se generan en cada ejecución y no se guardan en el repositorio.
