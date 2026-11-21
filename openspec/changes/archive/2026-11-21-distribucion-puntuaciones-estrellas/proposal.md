# Proposal

## Why

La distribución global de puntuaciones todavía presenta intervalos y mediana en la escala numérica de 0 a 10, mientras que la interfaz representa los puntajes como estrellas. Usar la misma escala facilita interpretar las métricas agregadas sin cambiar los resultados de análisis.

## What Changes

- Presentar los intervalos de la distribución global como rangos de 0 a 5 estrellas, en pasos de media estrella.
- Presentar también la mediana en estrellas, convertida desde el puntaje exacto y conservando dos decimales.
- Mantener el puntaje original sobre 10 para agrupar, calcular y almacenar los resultados.
- Limitar el cambio a la métrica administrativa «Distribución de puntuaciones»; no modificar los umbrales de filtros ni la distribución privada de la pantalla Análisis del aspirante.

## Capabilities

### New Capabilities

### Modified Capabilities
- `estadisticas-plataforma`: expresar en estrellas los intervalos y la mediana de la distribución global de puntajes.

## Impact

- Estadísticas globales del centro administrativo.
- Conversión de los intervalos y la mediana desde la escala interna 0–10 a la escala visible 0–5 estrellas.
