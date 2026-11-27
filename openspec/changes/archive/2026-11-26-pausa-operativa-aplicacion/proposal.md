# Proposal

## Why

La plataforma necesita una forma administrativa de pausar la carga automática y el análisis de vacantes, por ejemplo durante una pausa de staging o cuando no hay usuarios activos. La pausa debe reducir trabajo y consumo sin quitar el acceso al centro administrativo necesario para reanudarla.

## What Changes

- Añadir un control global para pausar y reanudar la búsqueda y el análisis de vacantes.
- Mantener disponibles el portal y las herramientas administrativas mientras la pausa esté activa.
- Definir qué ocurre con trabajos en cola y con el trabajo que ya esté ejecutándose.

## Capabilities

### New Capabilities
- `control-operativo-aplicacion`: Pausar y reanudar la búsqueda y el análisis en toda la plataforma.

### Modified Capabilities

## Impact

- Centro administrativo y parámetros operativos.
- Trabajos programados y encolados de ingesta y análisis.
- Comandos administrativos que pueden iniciar esos trabajos.
