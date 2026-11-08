# Plan de commits (inicio → fin)
| # | Mensaje | Archivos |
|---|---|---|
| 1 | `chore: estructura inicial del proyecto` | .gitignore, requirements.txt |
| 2 | `data: agrega CSV original de reservas 01-01-2024` | data/raw/Campos_Reservas_01-01-2024.csv |
| 3 | `feat: limpieza y análisis de reservas con variables derivadas` | scripts/01_limpieza_analisis.py + data/processed/* |
| 4 | `feat: dashboard interactivo con gráficas, mapa, pozos y glosario` | web/template.html, scripts/02_build_web.py, data/external/coordenadas_campos.csv, web/index.html |
| 5 | `feat: normalización de pozos, plantilla y datos de demostración` | scripts/03_normalizar_pozos.py, scripts/04_generar_demo_pozos.py, data/external/pozos_plantilla.csv, data/demo/pozos_DEMO_ficticio.csv |
| 6 | `feat: descargador de pozos desde el servicio ArcGIS de la CNH con prueba simulada` | scripts/05_descargar_pozos_arcgis.py, tests/test_05_arcgis_simulado.py |
| 7 | `docs: README, glosario, hallazgos, guía de pozos y capturas` | README.md, docs/* |
| 8 | `chore: configuración de VS Code (tareas, depuración, extensiones)` | .vscode/* |

Etiqueta final: `git tag v1.1`. Subir: `git remote add origin <url> && git push -u origin main --tags`.
Siguientes: pozos reales descargados, coordenadas reales de campos, comparar cortes anuales, publicar en GitHub Pages.
