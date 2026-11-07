# Proposal

## Why

El puntaje ayuda a priorizar recomendaciones, pero no refleja la urgencia de los procesos que ya avanzaron. Ordenar cada etapa de seguimiento por cuándo entró la vacante en ella pone primero los cambios más recientes.

## What Changes

- En Recomendaciones, ordenar por puntaje numérico descendente con precisión completa, incluidos los decimales.
- En Aplicadas, En proceso, Entrevista, Finalizadas y Descartadas, ordenar desde la entrada más reciente al estado hasta la más antigua.
- Mantener «Por analizar» fuera de ambos órdenes porque aún no tiene puntaje ni etapa de seguimiento.
- Mantener los filtros, pertenencia a estados y conteos independientes de la ordenación.

## Capabilities

### New Capabilities

### Modified Capabilities
- `dashboard-vacantes`: usar puntaje descendente en Recomendaciones y fecha de entrada al estado descendente en las etapas de seguimiento.

## Impact

- Consultas y presentación de listas en el dashboard por pestaña.
- Reutiliza el puntaje por perfil, la rúbrica decimal y la fecha de entrada al estado.
- Depende de las pestañas de seguimiento, los puntajes decimales y `fechas-relativas-vacantes`; debe completarse antes del despliegue a stage.
