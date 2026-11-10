# Proposal

## Why

La sección administrativa de disponibilidad puede sugerir que el sistema comprueba si una publicación sigue activa o fue cerrada en Elempleo. No se hará ese monitoreo, por lo que la estadística no debe presentarse.

## What Changes

- Retirar de estadísticas globales el conteo de publicaciones activas, cerradas y desconocidas.
- Mantener los estados personales de seguimiento, incluidos los descartes, separados de la disponibilidad externa.

## Capabilities

### New Capabilities

### Modified Capabilities
- `estadisticas-plataforma`: eliminar la estadística de disponibilidad externa de publicaciones.

## Impact

Afecta el resumen administrativo global y su cálculo. No cambia el scraper, los estados de seguimiento ni la selección de vacantes.
