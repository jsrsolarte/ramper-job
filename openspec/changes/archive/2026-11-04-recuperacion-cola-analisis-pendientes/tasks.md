# Tasks

## 1. Estado persistente y reclamación idempotente

- [x] 1.1 Añadir marcas de despacho, inicio/lease y contador de recuperaciones a `VacancyAnalysis`, con una migración compatible; verificar migración hacia delante y reversa sin modificar resultados existentes.
- [x] 1.2 Implementar la reclamación transaccional por análisis y la liberación del lease en éxito, fallo y reintento; verificar que dos entregas simultáneas produzcan una sola llamada al modelo.
- [x] 1.3 Añadir pruebas para entregas repetidas, análisis completados o reemplazados y leases vencidos; verificar que solo se ejecute un análisis vigente a la vez.

## 2. Reconciliación y reencolado

- [x] 2.1 Implementar una tarea periódica que busque pendientes elegibles sin despacho o ejecución reciente, con umbral y tamaño de lote configurables; verificar que excluya revisiones antiguas, vacantes inactivas y ubicaciones no elegibles.
- [x] 2.2 Registrar el despacho antes de publicar la tarea y recuperar de nuevo si el proceso cae entre persistencia y publicación; verificar recuperación después del umbral sin depender de inspeccionar Redis.
- [x] 2.3 Añadir el reconciliador a Celery Beat con valores predeterminados conservadores y documentar configuración local; verificar que el worker consuma la cola configurada y que el ciclo repetido no genere duplicados.
- [x] 2.4 Añadir pruebas del reconciliador para cola vacía, análisis huérfano, procesamiento activo y recuperación por lotes; verificar conteos y límites de lote.

## 3. Backoff y observabilidad

- [x] 3.1 Aplicar backoff y máximo de recuperaciones por análisis; verificar que fallas temporales se reintenten y que los casos agotados dejen de publicarse automáticamente.
- [x] 3.2 Registrar ejecuciones recuperadas y reintentos agotados con categorías seguras y conteos agregados; verificar que no se almacenen CV, prompts, respuestas completas ni credenciales.
- [x] 3.3 Mostrar recuperaciones y agotamientos en el panel administrativo existente; verificar permisos administrativos, estados sin datos y resúmenes seguros.

## 4. Integración

- [x] 4.1 Simular una tarea perdida y verificar el recorrido completo: pendiente persistente, recuperación por Beat, reclamación única y resultado completado visible en el dashboard.
- [x] 4.2 Simular una falla persistente de OmniRoute y verificar backoff, agotamiento visible y ausencia de reencolado infinito.

## 5. Reintentos hasta vencimiento

- [x] 5.1 Conservar el primer hallazgo por perfil y vacante entre revisiones y limitar reintentos por los días configurados, con espera creciente acotada y sin duplicar ejecuciones.
- [x] 5.2 Recuperar fallidos vigentes y descartar para el perfil los vencidos sin eliminar la vacante compartida ni interferir con estados de seguimiento avanzados.
- [x] 5.3 Mostrar en Por analizar el número de intentos fallidos de IA y verificar el comportamiento en recuperación y vencimiento.
