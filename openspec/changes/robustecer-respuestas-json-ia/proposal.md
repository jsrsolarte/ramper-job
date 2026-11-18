# Proposal

## Why

Respuestas de OmniRoute con JSON dentro de bloques Markdown provocaron reintentos y acumulación de análisis, incluso con las rúbricas v2 y v3. Es necesario recuperar el formato sin cambiar la evaluación ni debilitar la validación de la rúbrica.

## What Changes

- Solicitar salida estructurada con JSON Schema cuando la ruta de OmniRoute lo soporte y definir una alternativa compatible cuando no lo soporte.
- Retirar localmente los delimitadores de un único bloque Markdown completo y validar el JSON interior sin una llamada adicional de IA.
- Solo si el contenido sigue siendo sintácticamente inválido después de la normalización local, realizar como máximo una llamada de IA para reparar el formato, sin volver a evaluar ni inventar información.
- Conservar el resultado y la política de recuperación existentes cuando la reparación falle; registrar métricas seguras separadas.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `compatibilidad-vacantes`: interpretación y reparación limitada de respuestas de puntuación y organización.
- `observabilidad-operativa`: medición segura de normalización y reparación de formato.

## Impact

Afecta al cliente de OmniRoute, las tareas de puntuación y organización, sus validadores y métricas. Puede añadir una llamada de IA por respuesta sintácticamente inválida y depende de la compatibilidad efectiva del proveedor con salida estructurada. No incluye cambio de rúbrica, modelo, proveedor ni despliegue a producción.
