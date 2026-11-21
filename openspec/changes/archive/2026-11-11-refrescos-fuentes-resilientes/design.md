# Design

## Context

El refresco actual se ejecuta como una cadena de tareas Celery que puede hacer consultas de búsqueda y enriquecer fichas una tras otra. Los registros operativos ya guardan estado y métricas agregadas, pero no identifican de forma durable cada unidad pendiente, confirmada o interrumpida. Celery aplica un límite global de 15 minutos y la reconciliación actual no se ejecuta con la frecuencia necesaria para corregir enseguida los estados huérfanos. La motivación y el alcance están en `proposal.md`; los contratos están en las tres deltas de `specs/`.

## Goals / Non-Goals

**Goals:**

- Persistir el avance por unidad de búsqueda para poder reintentar sin repetir efectos ya confirmados.
- Mantener cada tarea por debajo del límite global, conservando el conjunto completo de combinaciones y las pausas de cada conector.
- Derivar el estado del refresco y del comando desde trabajo durable, y exponer únicamente progreso agregado.

**Non-Goals:**

- Cambiar el límite global de Celery o los criterios de búsqueda de las fuentes.
- Cambiar la política de análisis, la pausa global o la futura pausa individual por perfil.
- Rediseñar el pipeline independiente de recuperación de análisis de vacantes.

## Decisions

1. **Usar unidades de trabajo persistidas como fuente de verdad.** Crear registros durables asociados a una ejecución de fuente y a una combinación de consulta estable, con estado, intento, marca de progreso y resultado agregado. La identidad única de la unidad evita encolar duplicados. Las tareas Celery reciben el identificador de la unidad y reclaman su lease antes de procesarla. Se elige esto frente a depender solo de mensajes encadenados o de inspección de workers: la cola puede perder o repetir mensajes y la inspección no representa de forma fiable trabajo que aún está en cola.

2. **Acotar cada tarea con lotes conservadores y continuaciones.** La preparación de términos corre en una tarea por perfil. Luego, cada unidad consulta un término para un bloque de hasta seis ubicaciones (incluida la búsqueda remota una sola vez), aplica el filtro de títulos y enriquece hasta cinco fichas. Los límites tienen configuración de entorno y máximos seguros; si quedan fichas, se persiste el cursor y se encola la continuación. Con los timeouts actuales, estos tamaños dejan margen amplio frente al límite de 15 minutos y se pueden reducir en staging según el tiempo observado.

3. **Confirmar resultados de forma idempotente.** Guardar cada página, vacante normalizada, asociación, seguimiento y checkpoint en transacciones acotadas; usar las claves de deduplicación existentes y una clave estable de unidad/página para que reintentar sea seguro. Los análisis continúan siendo por perfil y revisión, y no se vuelven a solicitar si ya existe el resultado correspondiente. Una unidad solo avanza su cursor después de confirmar sus efectos.

4. **Separar el progreso de la ejecución del progreso privado del perfil.** Agregar contadores confirmados por fuente (unidades, consultas/páginas y vacantes) al registro operativo existente o a una relación agregada equivalente. No guardar términos ni ubicaciones en el payload visible del dashboard. Los comandos administrativos agregan los estados de las unidades asociadas; los reintentos no reinician contadores confirmados.

5. **Reconciliar usando estado durable y heartbeats.** Ejecutar una tarea ligera de reconciliación cada cinco minutos, separada de la limpieza histórica diaria. Marcar una ejecución y su comando como fallidos o parciales solo cuando haya pasado el umbral de 20 minutos sin heartbeat/progreso y no existan unidades pendientes con lease vigente. Liberar leases vencidos y dejar que las unidades reintentables vuelvan a cola. No usar únicamente `inspect active` de Celery para decidir que no queda trabajo.

6. **Desplegar aditivamente y mantener compatibilidad.** Agregar primero esquema y campos nullable/defaulted, desplegar workers que entiendan tanto ejecuciones existentes como nuevas, y luego activar el despacho por unidades. Las ejecuciones históricas conservan sus métricas; no se inventan checkpoints para ellas. Se mantiene intacto el límite de 15 minutos.

## Risks / Trade-offs

- **Más filas y mensajes Celery por refresco** → indexar identidad/estado/lease, limitar el tamaño de las unidades y conservar la política existente de retención histórica.
- **Duplicados durante reintentos o entrega al menos una vez** → confirmar efectos y checkpoint de manera transaccional, y conservar claves idempotentes para vacantes, asociaciones, seguimientos y análisis.
- **Los límites de llamadas externas pueden variar por fuente** → permitir tamaño de unidad configurable y comprobar el presupuesto antes de cada llamada; usar límites conservadores hasta observar staging.
- **La reconciliación podría cerrar trabajo lento que aún es válido** → considerar leases y heartbeat de cada unidad, y aplicar el umbral únicamente si no queda trabajo vigente.
- **Un despliegue interrumpido puede mezclar productores y workers de versiones distintas** → desplegar esquema compatible antes que el nuevo productor y verificar que las tareas antiguas sigan siendo consumibles durante la transición.

## Migration Plan

1. Aplicar migraciones aditivas para unidades de trabajo, índices, leases y progreso agregado; desplegar y verificar que los servicios existentes arrancan con el esquema nuevo.
2. Desplegar workers con los handlers de unidades y reconciliación, manteniendo el productor anterior desactivado para el flujo nuevo.
3. Activar el despacho acotado en staging; verificar avance visible, cobertura completa, deduplicación y recuperación de una unidad interrumpida antes de completar la validación de `agregar-computrabajo`.
4. Ante una regresión, detener la creación de unidades nuevas y volver al productor anterior. Mantener las tablas/campos aditivos hasta terminar las ejecuciones en curso; no borrar historial ni checkpoints automáticamente.
5. Promover a producción solo mediante el proceso habitual y con autorización explícita; esta propuesta no autoriza una promoción.
