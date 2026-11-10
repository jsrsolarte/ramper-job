# Proposal

## Why

Las búsquedas pueden devolver listas grandes y actualmente se consulta la ficha completa y se programa el análisis de cada vacante elegible antes de saber si el cargo tiene relación con la búsqueda. Un filtro conservador por título puede evitar ese trabajo para las vacantes claramente ajenas y reservar el análisis detallado para candidatas plausibles.

## What Changes

- Antes de consultar las fichas completas, enviar en lote los títulos encontrados y los términos compartidos de cada solicitud de búsqueda a la IA.
- Descartar solo títulos que no tengan relación laboral clara con la búsqueda; conservar los compatibles y los dudosos para el flujo actual.
- Aplicar la decisión a los perfiles que comparten esa solicitud de búsqueda, sin enviar sus CV ni mezclar datos de solicitudes diferentes.
- Si el filtro falla o no produce una decisión válida para un título, conservar esa vacante y continuar con el flujo normal.
- Mantener el registro manual de vacantes desde URL fuera del filtro.
- Mostrar por consulta el embudo desde títulos encontrados hasta resultados posteriores al análisis, con las duraciones expresadas en minutos.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `ingesta-vacantes`: preseleccionar resultados automáticos por título antes de extraer la ficha y programar análisis, preservando candidatas dudosas y el flujo manual existente.

## Impact

- Afecta el flujo de búsqueda de conectores y la programación compartida de fichas y análisis.
- Añade una etapa por lote de títulos y términos de búsqueda antes de la extracción detallada.
- Reduce consultas de fichas públicas y llamadas de puntuación cuando los títulos son claramente incompatibles, con una regla conservadora para evitar falsos descartes.
