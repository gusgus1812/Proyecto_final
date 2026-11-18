# Fuente del mapa de hidrocarburos
Sitio: https://mapa-hidrocarburos.energia.gob.mx/ (CNH/SENER). La página principal que pude leer solo traía metadatos y un aviso de mantenimiento; no pude acceder a sus capas desde mi entorno.

**Pozos:** ver `docs/pozos.md` (servicio ArcGIS «Pozos, 2024» y `scripts/05_descargar_pozos_arcgis.py`). Cada pozo baja con su latitud y longitud, así que **una vez descargado el CSV el mapa de pozos ya no depende de la página**.

## Dónde se ubican los campos
1. **Automático (recomendado):** al cargar los pozos, el mapa coloca cada campo en la **mediana de las coordenadas de sus pozos**. No necesitas ningún archivo extra y cubre todos los campos que tengan pozos.
2. **Guardarlo en CSV:** `python3 scripts/06_coordenadas_campos_desde_pozos.py` escribe ese cálculo en `data/external/coordenadas_campos.csv` (nombre, lat, lon, nota con el número de pozos y la extensión aproximada). 
3. **Sin pozos:** el archivo incluido tiene 7 posiciones aproximadas puestas de memoria (±50 km o más) solo para probar el mapa. Con pozos cargados se reemplazan solas.
Limitación: el centro de los pozos es un **punto**, no el contorno real del campo.

## ¿Y un shapefile?
Un shapefile (o GeoJSON) aporta lo que los puntos no pueden: **polígonos** con el contorno de campos, asignaciones o contratos. Ayudaría a dibujar el área real de cada campo en lugar de un punto.
- **Dónde conseguirlo:** en el mapa de la CNH o en el servicio ArcGIS suele haber opción de exportar/descargar las capas; también las capas de ArcGIS se pueden pedir como GeoJSON con `f=geojson` en la consulta `/query`. No pude verificar qué descargas ofrece la CNH.
- **Cómo usarlo aquí:** el mapa del dashboard (Leaflet) dibuja GeoJSON directamente. Un shapefile habría que convertirlo a GeoJSON (con `pyshp` o `geopandas`, que se instalan con pip en tu computadora). Ojo: los shapefiles oficiales de México a veces vienen en coordenadas proyectadas (por ejemplo ITRF2008 / cónica conforme de Lambert) y hay que reproyectarlos a latitud/longitud (WGS84) antes de dibujarlos.
- **Si lo consigues:** pásame el archivo `.zip` del shapefile (o el GeoJSON) y agrego el dibujo de contornos de campo al mapa.
