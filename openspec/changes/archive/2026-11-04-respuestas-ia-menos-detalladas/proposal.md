# Proposal

## Why

Las llamadas de análisis pueden producir explicaciones y descripciones más detalladas de lo necesario, aumentando los tokens de salida. Pedir a la IA solo la información clave reduce ese consumo y mantiene lo necesario para entender y comparar las vacantes.

## What Changes

- Ajustar las instrucciones de puntuación para conservar el desglose requerido y devolver solo evidencia y razones principales, sin explicaciones extensas o repetidas.
- Ajustar la organización de vacantes para conservar resumen, palabras clave y categorías útiles con menos detalle secundario.
- Mantener el contenido respaldado por la publicación y el perfil, sin fijar un límite de caracteres ni eliminar campos necesarios para el puntaje.

## Capabilities

### New Capabilities

### Modified Capabilities
- `compatibilidad-vacantes`: reducir el detalle narrativo solicitado en resultados de puntuación manteniendo el desglose y la evidencia necesarios.
- `presentacion-vacantes`: reducir detalles secundarios en el contenido organizado por IA conservando la información principal.

## Impact

- Prompts versionados para puntuación y organización de vacantes.
- Formato de respuesta y contenido guardado por ambas etapas de IA; no requiere cambiar los criterios de la rúbrica ni aplicar un máximo de longitud.
