# Proposal

## Why

Los análisis pueden quedar pendientes cuando una respuesta del modelo no cumple la rúbrica, pero hoy solo se conserva un mensaje genérico. La administración necesita saber qué regla de validación falló para corregir el prompt o el formato sin guardar respuestas del modelo ni datos del perfil.

## What Changes

- Clasificar los rechazos de validación con códigos seguros y específicos de la estructura o regla que falló.
- Hacer visibles en las métricas administrativas los motivos agregados de rechazo de respuestas de análisis.
- Conservar los mensajes de error del aspirante sin detalles técnicos ni datos privados.
- Mantener el puntaje, la rúbrica y la política vigente de reintentos sin cambios.

## Capabilities

### New Capabilities

### Modified Capabilities
- `observabilidad-operativa`: distinguir y consultar los motivos seguros de respuestas de IA que no cumplen el esquema.

## Impact

- Validación de respuestas y registro de intentos en `matching`.
- Métricas de análisis del centro administrativo.
- No requiere guardar prompts, CV ni respuestas completas del modelo.
