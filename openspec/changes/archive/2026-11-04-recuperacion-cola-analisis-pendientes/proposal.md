# Proposal

## Why

Durante la prueba local quedaron análisis marcados como pendientes en la base de datos, aunque sus tareas ya no estaban en las colas de Celery. El panel operativo muestra cantidad y antigüedad, pero el sistema no recupera ese trabajo; se tuvo que reencolar manualmente.

## What Changes

- Añadir una reconciliación periódica que encuentre análisis vigentes pendientes sin despacho o ejecución reciente y los vuelva a encolar.
- Hacer el despacho y la toma del trabajo idempotentes para evitar análisis paralelos o duplicados.
- Limitar reintentos y registrar recuperaciones y agotamiento de intentos con métricas y errores saneados.
- Recuperar únicamente análisis activos que correspondan a la revisión, configuración y ubicación actuales del perfil.

## Capabilities

### New Capabilities

- `recuperacion-trabajos-analisis`: detección y recuperación segura de análisis que se pierden o quedan sin progreso en segundo plano.

### Modified Capabilities

- `compatibilidad-vacantes`: precisar cómo se conserva y reintenta un análisis pendiente cuando falla o se interrumpe su procesamiento.

## Impact

La recuperación continuará hasta el vencimiento por perfil, contado desde el primer hallazgo y usando los días configurados de descarte; la tarjeta mostrará el número de intentos. Un vencimiento no elimina la vacante compartida con otros perfiles.

- Tareas y configuración de Celery Beat, el ciclo de vida de `VacancyAnalysis` y su persistencia.
- Registros operativos para medir análisis recuperados y plazos vencidos.
- Dashboard administrativo para identificar trabajo recuperado o que requiere atención; el dashboard de aspirantes mantiene los resultados pendientes claramente diferenciados.
