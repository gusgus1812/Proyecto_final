# Pozos: de dónde salen y cómo cargarlos

## Qué sé de la fuente (y qué no)
- El **Mapa de Hidrocarburos** de la CNH muestra, al hacer clic en un pozo, una ficha con: POZO, CAMPO, ENTIDAD, UBICACIÓN, CLASIFICACIÓN, ESTADO ACTUAL, TIPO DE HIDROCARBURO, FECHA INICIO/FIN PERFORACIÓN, PROFUNDIDAD TOTAL, PROFUNDIDAD VERTICAL, TRAYECTORIA, DISPONIBLE y CAPA (zona). Ese es el esquema que usa este proyecto.
- Existe un servicio público de ArcGIS con exactamente esos campos: capa **«Pozos, 2024»** (datos de la CNH / CNIH, alojada en el servidor de SEMARNAT):
  `https://geomaticasig1.semarnat.gob.mx/arcgis/rest/services/Hosted/Pozos_2024/FeatureServer/0`
  Campos del servicio: `pozo, campo, entidad, ubicacin, clasificac, estado_act, tipo_de_hi, fecha_inic, fecha_fin_, profundida, profundi_1, trayectori, disponible, pozos (zona)`; máximo 2000 registros por consulta.
- **Lo que NO pude comprobar:** desde el entorno donde armé el proyecto no hay acceso a ese servidor, así que no sé cuántos pozos trae ni qué zonas cubre (la descripción del servicio habla de la zona de aguas profundas, pero su lista de zonas incluye Burgos y Veracruz). Tampoco puedo asegurar que sea exactamente la misma capa que usa el mapa. El descargador la prueba contra un servidor simulado (`tests/test_05_arcgis_simulado.py`), no contra el real. Al correrlo en tu computadora verás el total y las zonas; si faltan campos, usa la ruta de abajo.

## Paso a paso (con internet)
```bash
python3 scripts/05_descargar_pozos_arcgis.py                       # todos los pozos de la capa
python3 scripts/05_descargar_pozos_arcgis.py --campo IXACHI AKAL   # o solo algunos campos
python3 scripts/03_normalizar_pozos.py data/external/pozos_arcgis_crudo.csv
python3 scripts/02_build_web.py
```
Abre `web/index.html` → pestaña **Pozos** → escribe o elige un campo (o haz clic en un campo en cualquier gráfica).

Notas:
- El mapa incluye campos que **no están** en los 477 del archivo de reservas (no todos tienen reservas) y pozos sin campo: el normalizador los reporta en `data/processed/pozos_sin_campo.csv`. Es normal.
- Sin campo seleccionado, el mapa dibuja los pozos solo si hay menos de 6,000; con más, pide elegir un campo.
- Si el archivo es muy grande, el navegador no podrá recordar los pozos cargados a mano (límite de almacenamiento); por eso conviene dejarlos en `data/external/pozos.csv` y regenerar la web.

## Si esa capa no trae todo: encontrar el servicio que usa el mapa
1. Abre el mapa en tu navegador → F12 → pestaña **Red / Network** → filtra por `query`.
2. Haz clic en un pozo. Aparecerá una petición que termina en `/FeatureServer/<n>/query` o `/MapServer/<n>/query`.
3. Copia la URL hasta `<n>` y pásala al descargador (acepta varias; también un servicio completo, y descarga todas sus capas de puntos con campo `pozo`):
```bash
python3 scripts/05_descargar_pozos_arcgis.py URL_CAPA_1 URL_CAPA_2
```
Revisa los términos de uso del sitio antes de descargar datos en volumen.

## Formato canónico (data/external/pozos_plantilla.csv)
`pozo,campo,entidad,ubicacion,clasificacion,estado,tipo_hidrocarburo,fecha_inicio,fecha_fin,profundidad_total_m,profundidad_vertical_m,trayectoria,disponible,capa,lat,lon`
Solo `pozo` y `campo` son obligatorios. El normalizador acepta los encabezados de la ficha del mapa (`ESTADO ACTUAL`, `PROFUNDIDAD TOTAL`…), los nombres crudos del servicio (`estado_act`, `profundida`…) y otros alias comunes; las fechas `01-AGO-2021` se convierten a `2021-08-01`.

## Cómo se decide activo / inactivo
Se lee el texto de `ESTADO ACTUAL`:
- **Inactivo** si contiene: inactivo, no productor, cerrado, taponado, abandonado, suspendido, improductivo, seco, sin producción, en espera, desmantelado.
- **Activo** si contiene: productor, activo, operando, inyector, fluyente, bombeo, en operación.
- **Sin dato** en cualquier otro caso (por ejemplo «en perforación»). El texto original siempre se muestra, y la gráfica «Estado actual (texto original)» te deja ver todos los valores que trae el archivo.
Si ves estados mal clasificados, ajusta `statusClass()` en `web/template.html` y `clase_estado()` en `scripts/03_normalizar_pozos.py`.

## Qué se puede comparar
Hasta 6 pozos lado a lado: estado, clasificación, entidad, capa, trayectoria, fechas, **días de perforación**, **profundidad total**, **profundidad vertical** y **desviación** (total − vertical), con el porcentaje frente al promedio de su campo. El mapa no trae producción por pozo, así que el dashboard no la muestra.
