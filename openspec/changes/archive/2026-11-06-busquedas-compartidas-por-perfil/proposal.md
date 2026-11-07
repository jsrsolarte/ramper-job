# Proposal

## Why

Hoy las búsquedas de vacantes se ejecutan separadas para cada perfil, incluso cuando usan los mismos términos, ubicaciones y modalidad. Agrupar solo las consultas equivalentes reduce llamadas repetidas a las fuentes sin mezclar los puntajes, resultados ni estados personales.

## What Changes

- Agrupar perfiles cuyas solicitudes de búsqueda tengan criterios efectivos equivalentes y consultar una sola vez por grupo y fuente.
- Mantener una publicación global única por vacante encontrada y vincularla a cada perfil del grupo que la encontró.
- Crear o reutilizar un análisis independiente para cada perfil vinculado, aplicando su CV, preferencias y rúbrica completa.
- Mantener el seguimiento y los estados separados por perfil, sin compartir decisiones personales.

## Capabilities

### New Capabilities

### Modified Capabilities
- `busqueda-por-perfil`: agrupar solicitudes equivalentes y distribuir los resultados a los perfiles del grupo.

## Impact

- Cambios en la programación de búsquedas periódicas y manuales y en el fan-out de resultados hacia análisis por perfil.
- Reutiliza las capacidades existentes de deduplicación global, compatibilidad por perfil y seguimiento personal.
- Debe implementarse después de los cambios funcionales de perfil, deduplicación, rúbrica y seguimiento que necesita, y antes del despliegue a stage.
