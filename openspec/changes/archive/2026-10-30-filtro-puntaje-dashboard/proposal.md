# Proposal

## Why

El puntaje mínimo guardado en el perfil define qué vacantes son elegibles para esa persona. En el dashboard hace falta un control aparte para afinar la lista del momento, sin modificar la preferencia guardada ni mostrar vacantes que el perfil excluye.

## What Changes

- Agregar al dashboard un filtro temporal por puntaje mínimo, disponible junto al listado de vacantes.
- Combinar el filtro del listado con el mínimo del perfil: la lista solo puede estrechar el conjunto permitido por el perfil.
- Conservar la selección del listado en la URL para que funcione al cambiar de página y al recargar.
- Mantener el mínimo guardado exclusivamente en la configuración del perfil.

## Capabilities

### New Capabilities

### Modified Capabilities
- `dashboard-vacantes`: permitir filtrar en el dashboard por puntaje sin cambiar el mínimo guardado en el perfil.

## Impact

- `dashboard/views.py` y la plantilla del dashboard para leer, validar y aplicar el filtro temporal.
- Controles visuales y estilos del listado; no se requieren migraciones ni cambios al modelo de perfil.
