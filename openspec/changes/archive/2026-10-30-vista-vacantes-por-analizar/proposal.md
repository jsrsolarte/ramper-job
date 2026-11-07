# Proposal

## Why

La persona no puede consultar las publicaciones originales que aún esperan análisis de IA desde el dashboard. Una bandeja separada le permitirá revisar las vacantes encontradas y sus datos fuente mientras el análisis sigue pendiente.

## What Changes

- Añadir una pestaña privada de vacantes con análisis pendiente para el perfil y revisión vigentes, con el conteo de vacantes visibles.
- Presentar los datos originales disponibles y el enlace a la publicación, sin mostrar resultados de IA que aún no existen.
- Integrar la pestaña en la navegación común de vacantes junto con recomendaciones y estados de seguimiento, en orden de flujo lógico.

## Capabilities

### New Capabilities

### Modified Capabilities

- `dashboard-vacantes`: incluir una vista raw de vacantes que esperan análisis para el perfil actual.

## Impact

- Vista, rutas y plantilla del dashboard.
- No requiere cambios al scraping, al análisis de IA ni al modelo de seguimiento de postulaciones.
