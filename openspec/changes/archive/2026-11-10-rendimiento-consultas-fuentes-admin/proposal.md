# Proposal

## Why

La tarjeta de disponibilidad de publicaciones se retiró porque la aplicación no verifica si una vacante sigue abierta. Ese espacio puede mostrar información operativa útil: cuánto tardan las consultas automáticas por fuente y con qué frecuencia terminan sin éxito.

## What Changes

- Añadir a estadísticas globales un resumen por fuente de las ejecuciones `source_query` terminadas dentro del periodo seleccionado.
- Mostrar cantidad de ejecuciones, duración mediana, percentil 95 y porcentaje de ejecuciones no exitosas.
- Ubicar el resumen junto al seguimiento por perfil, sin duplicar el historial cronológico de Observabilidad.

## Capabilities

### New Capabilities

### Modified Capabilities
- `estadisticas-plataforma`: incluir métricas agregadas de duración y resultado de consultas automáticas por fuente.

## Impact

- `operations/platform_statistics.py`: agregación acotada por periodo, fuente y tipo de operación.
- `operations/templates/operations/platform_statistics.html` y `static/app.css`: presentación de la tabla y composición responsive.
- Sin cambios de esquema de base de datos ni de la lógica de scraping.
