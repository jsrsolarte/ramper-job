# Proposal

## Why

La administración necesita entender cómo se distribuyen las vacantes entre los estados de seguimiento y qué distribución de puntajes produce el análisis de IA en toda la plataforma. Las métricas por perfil ayudan a cada aspirante a ajustar su filtro, pero no muestran el comportamiento agregado del servicio.

## What Changes

- Añadir estadísticas administrativas agregadas de los estados de seguimiento y disponibilidad de publicaciones.
- Mostrar la distribución de puntuaciones de compatibilidad, conservando los decimales y el tamaño de muestra.
- Permitir consultar los puntajes por periodos definidos y señalar la cobertura de los datos disponibles.
- Integrar estas estadísticas en el centro administrativo sin duplicar las métricas operativas de colas, duración y fallos.
- Evitar que gráficos o agregaciones revelen CV, perfiles identificables o contenido de vacantes.

## Capabilities

### New Capabilities

- `estadisticas-plataforma`: estadísticas de negocio agregadas de vacantes y puntuaciones para administración.

### Modified Capabilities

## Impact

- Consultas agregadas sobre seguimiento y estado de publicación de vacantes.
- Estadísticas de resultados de compatibilidad por periodos, con puntajes decimales.
- Centro administrativo y controles de privacidad para vistas globales.
