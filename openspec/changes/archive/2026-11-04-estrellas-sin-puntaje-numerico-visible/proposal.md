# Proposal

## Why

El valor como `7/10` junto a las estrellas repite la calificación y recarga visualmente cada tarjeta. Mostrar solo las estrellas hace que la valoración se lea de un vistazo sin quitar el puntaje exacto de accesibilidad ni de las funciones que lo usan.

## What Changes

- Quitar la fracción numérica visible junto o debajo de las estrellas de compatibilidad en las tarjetas de vacantes.
- Mantener las estrellas como representación visual y el puntaje exacto en la etiqueta accesible.
- Conservar el valor numérico para filtros, orden y detalle del desglose.

## Capabilities

### New Capabilities

### Modified Capabilities
- `dashboard-vacantes`: mostrar en las tarjetas solo las estrellas, sin la fracción visible sobre 10.

## Impact

- Presentación del puntaje de compatibilidad en las tarjetas del dashboard.
- No cambia el puntaje calculado, la rúbrica, el orden, los filtros ni el desglose por criterios.
