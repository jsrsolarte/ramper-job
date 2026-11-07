# Proposal

## Why

Las estrellas del perfil se presentan como un puntaje mínimo que filtra recomendaciones, mientras que el producto necesita que expresen qué tan baja puede ser la compatibilidad antes de descartar automáticamente una vacante. Además, los cambios al umbral deben afectar las nuevas vacantes sin alterar seguimientos ya creados ni reactivar descartes.

## What Changes

- Cambiar la etiqueta y ayuda de las estrellas del perfil para comunicar que son el umbral de descarte automático.
- Guardar el umbral vigente cuando una vacante se descubre por primera vez para un perfil y descartar las puntuaciones inferiores al terminar su análisis.
- Mantener sin cambios los seguimientos existentes cuando se actualice el umbral; los descartes automáticos permanecen en la pestaña Descartadas.
- Separar este umbral del filtro de estrellas del listado, que continúa siendo un filtro temporal independiente.

## Capabilities

### New Capabilities

### Modified Capabilities

- `preferencias-busqueda-perfil`: las estrellas definen el umbral de descarte para nuevas vacantes, no un filtro retroactivo.
- `dashboard-vacantes`: las recomendaciones reflejan estados de seguimiento y el filtro del listado es independiente del umbral del perfil.
- `seguimiento-postulaciones`: los análisis nuevos bajo el umbral guardado al descubrir la vacante pasan a Descartadas automáticamente.

## Impact

- Perfil y formulario de edición; consulta del dashboard y filtro temporal de estrellas.
- Descubrimientos perfil-vacante, creación y finalización de análisis, seguimiento de vacantes.
- Migración para conservar los umbrales previos sin reevaluar descubrimientos existentes.
