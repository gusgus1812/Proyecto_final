# Fuente del mapa de hidrocarburos
Sitio: https://mapa-hidrocarburos.energia.gob.mx/ (CNH/SENER). La página principal que pude leer solo traía metadatos y un aviso de mantenimiento; no pude acceder a sus capas desde mi entorno.

**Pozos:** ver `docs/pozos.md` (servicio ArcGIS «Pozos, 2024» y `scripts/05_descargar_pozos_arcgis.py`).

**Coordenadas de los campos:** el mapa tiene capa de campos; se pueden obtener igual que los pozos (F12 → Red → clic en un campo → URL `/query`). Guarda un CSV `nombre,lat,lon` en `data/external/coordenadas_campos.csv` y ejecuta `python3 scripts/02_build_web.py`, o cárgalo desde la pestaña Mapa. Los nombres deben coincidir con los del CSV de reservas (mayúsculas, sin acentos).

**Nota:** `data/external/coordenadas_campos.csv` incluido tiene 7 posiciones aproximadas puestas de memoria (±50 km o más). Sirven solo para probar el mapa; reemplázalas.
