# Design

## Context

Ver `proposal.md` y los contratos en `specs/`. `VacancyAnalysis` usa los estados pendiente, completado y reemplazado. Celery Beat ya ejecuta el reprocesamiento de análisis antiguos y la limpieza operativa; esta última cierra ejecuciones `running` de más de 20 minutos, pero no vuelve a encolar análisis. En la prueba local había análisis vigentes pendientes con ambas colas de Redis vacías. Por eso Redis no puede ser la única fuente para decidir qué trabajo existe.

## Goals / Non-Goals

**Goals:**
- Usar la base de datos como fuente de verdad para recuperar trabajo perdido y limitar concurrencia por análisis.
- Recuperar en lotes pequeños y respetar revisión, configuración, vigencia y elegibilidad de ubicación.
- Hacer visibles las recuperaciones, los intentos y los vencimientos con métricas operativas saneadas.

**Non-Goals:**
- Reintentar automáticamente todas las fallas de ingesta o reemplazar el broker Celery/Redis.
- Inspeccionar o manipular directamente las estructuras internas de Redis para inferir el estado real del trabajo.
- Volver a analizar resultados completados sin una solicitud explícita de reprocesamiento.

## Decisions

### La base de datos será la fuente de verdad

Añadir a cada análisis marcas persistentes de último despacho, inicio de ejecución/lease y recuperaciones realizadas. Un reconciliador periódico buscará análisis pendientes cuyo despacho o ejecución haya superado el umbral configurado y volverá a publicarlos por Celery. El reconciliador consultará solo revisiones actuales, vacantes activas y ubicaciones elegibles; aplicará tamaño máximo de lote y espera creciente. No dependerá de `celery inspect`, que solo ofrece una fotografía momentánea del broker y los workers.

Alternativa considerada: usar únicamente la antigüedad de `updated_at` y volver a publicar el análisis. Se descarta porque no distingue una tarea entregada de una ejecución activa y puede generar varias llamadas simultáneas al modelo.

### Despacho y toma tendrán protección idempotente

La selección para recuperar y la toma del análisis por un worker usarán transacciones y bloqueo condicional. El despacho persistirá su marca antes de publicar la tarea; si el proceso cae entre ambos pasos, el siguiente ciclo recuperará el análisis al vencer el umbral. El worker obtendrá un lease por análisis antes de llamar a OmniRoute. Entregas repetidas, análisis ya completados y reemplazados terminarán sin generar otra llamada. Un lease vencido podrá reclamarse después de un margen superior al límite normal de ejecución.

Alternativa considerada: añadir solo identificadores de tarea Celery a `OperationalRun`. Se descarta como única protección porque una tarea puede perderse antes de crear el registro operativo y un registro de ejecución puede quedar obsoleto si el proceso muere.

### Los reintentos estarán limitados por vigencia y serán observables

Los pendientes se reintentan con espera creciente limitada, hasta alcanzar los días configurados de descarte desde el primer análisis de la pareja perfil-vacante, incluso tras cambiar la revisión. El contador visible suma las llamadas fallidas al modelo; el vencimiento descarta únicamente para ese perfil. Los fallidos existentes vigentes vuelven a ser elegibles, sin duplicar trabajos activos.

El backoff tiene un techo para evitar esperas crecientes sin límite y la vigencia limita el coste de una falla persistente.

### La migración será gradual

Los campos nuevos serán compatibles con registros existentes. Tras desplegar la migración y el reconciliador, los análisis antiguos pendientes se considerarán candidatos solo después del umbral inicial y se procesarán por lotes; no se hará un backfill que encole todo de una vez. La reversión desactiva el beat de recuperación y elimina los campos nuevos, dejando los resultados de análisis intactos.

## Risks / Trade-offs

- [El worker puede caer después de publicar y antes de liberar el lease] → Permitir que un lease vencido vuelva a ser reclamado y registrar el intento de recuperación.
- [Un umbral corto puede publicar duplicados mientras una tarea espera en cola] → La toma idempotente garantiza una sola llamada activa; usar lote limitado y umbral configurable.
- [La recuperación añade consultas periódicas sobre análisis] → Indexar campos de estado/tiempo usados por el reconciliador y limitar cada ciclo.
- [Una respuesta inválida persistente puede consumir llamadas] → Limitar la frecuencia mediante backoff y detener los reintentos al vencer el plazo por perfil.

## Migration Plan

1. Agregar los campos persistentes y sus índices con una migración compatible con registros existentes.
2. Implementar la toma idempotente y la finalización/liberación del lease en todas las rutas de éxito, fallo y reintento.
3. Añadir el reconciliador por lotes a Celery Beat y desplegarlo después de la migración.
4. Verificar recuperación, deduplicación concurrente, backoff, vencimiento por perfil y exclusiones por revisión o ubicación.
5. Para revertir, desactivar primero la tarea periódica; después revertir el código y la migración, sin borrar análisis ni historial operativo.
