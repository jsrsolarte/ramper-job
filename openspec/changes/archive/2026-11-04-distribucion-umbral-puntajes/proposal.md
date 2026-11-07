# Proposal

## Why

El usuario solo ve las vacantes que superan sus filtros y no puede entender cómo se distribuyen los demás puntajes. Una distribución y una sugerencia basada en sus resultados le ayudarán a decidir si conviene ajustar el mínimo.

## What Changes

- Mostrar la distribución de puntajes vigentes del perfil, incluyendo resultados por debajo del filtro actual.
- Ubicar la distribución debajo del listado de vacantes para mantener las oportunidades como foco principal.
- Sugerir un umbral entero a partir de la mediana, indicar cuántas vacantes conservaría y explicar el cálculo.
- Permitir aplicar la sugerencia al filtro de la sesión por decisión expresa del usuario, sin guardar el perfil automáticamente.
- Mantener los umbrales guardados y temporales como enteros entre 0 y 10.

## Capabilities

### New Capabilities

### Modified Capabilities

- `dashboard-vacantes`: mostrar distribución y sugerencia de puntaje con acción explícita para ajustar el filtro.

## Impact

- Cálculo agregado por perfil y revisión vigente, consulta del dashboard y controles de filtro.
- Sin cambios a la rúbrica ni al umbral guardado en el perfil.
