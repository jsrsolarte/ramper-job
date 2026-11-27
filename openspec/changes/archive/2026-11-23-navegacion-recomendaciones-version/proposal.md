# Proposal

## Why

La navegación principal no ofrece un enlace rotulado a Recomendaciones, aunque esa es la pantalla central de las personas aspirantes. Además, las versiones de producción se identifican y publican, pero la aplicación no las muestra, lo que dificulta reconocer qué versión está desplegada.

## What Changes

- Añadir «Recomendaciones» a la navegación principal de aspirantes, al lado de «Mi perfil».
- Mostrar en un pie de página común la versión correspondiente al artefacto que está ejecutándose.
- Presentar la versión semántica de producción y un identificador de commit para builds de staging, que no reciben versión de producto.
- Mantener una versión semántica canónica en `VERSION`, que el agente incrementa según el tipo de cambio antes de entregar la implementación.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `dashboard-vacantes`: actualizar la navegación principal para ofrecer acceso directo a Recomendaciones junto a Mi perfil.
- `versionado-liberaciones`: mostrar en la interfaz la versión de producción o el identificador del build de staging correspondiente al artefacto desplegado.

## Impact

- Afecta la plantilla compartida de navegación y el pie de página.
- Requiere entregar a la aplicación los metadatos de versión del artefacto ya construido, respetando que staging se identifica por SHA y no usa versiones de producto. Producción toma la versión del archivo `VERSION` incluido en el mismo código probado.
