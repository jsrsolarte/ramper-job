# Proposal

## Why

Una persona puede descartar una vacante y luego encontrarla de nuevo cuando una búsqueda la vuelve a obtener o un análisis se ejecuta otra vez. Ese descarte es una decisión por perfil y debe seguir aplicándose a la misma publicación, para que no reaparezca como recomendación.

## What Changes

- Mantener el estado descartado por perfil al volver a ingerir o analizar la misma vacante.
- Excluir vacantes descartadas de Recomendaciones y de sus conteos aunque tengan un análisis nuevo o mejorado.
- Permitir que solo una restauración explícita de la persona devuelva la vacante a su estado anterior.
- Conservar estados independientes cuando varios perfiles comparten una vacante.

## Capabilities

### New Capabilities

### Modified Capabilities

- `ingesta-vacantes`: actualizar la publicación compartida sin reiniciar el seguimiento de cada perfil.
- `dashboard-vacantes`: no mostrar vacantes descartadas como recomendaciones.

## Impact

- Upsert y deduplicación de vacantes conocidas durante el scraping.
- Creación y actualización de análisis por perfil.
- Consultas, conteos y transiciones de seguimiento del dashboard.
- Pruebas de regresión para reingesta, reanálisis, perfiles compartidos y restauración manual.
