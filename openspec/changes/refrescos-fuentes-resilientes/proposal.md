# Proposal

## Why

Una búsqueda puede combinar muchos términos y ubicaciones, consultar fichas y procesar fuentes en serie, superando el límite de ejecución de Celery de 15 minutos. Cuando Celery termina la tarea por ese límite, los registros de operación y el comando administrativo pueden quedar como «en curso» aunque ya no haya trabajo activo.

## What Changes

- Dividir la actualización de fuentes en unidades acotadas y reanudables, conservando todas las combinaciones de búsqueda, el orden y aislamiento de las fuentes y la deduplicación existente.
- Guardar progreso agregado por fuente y avanzar desde el último punto confirmado al reintentar, sin duplicar vacantes, seguimientos ni análisis.
- Cerrar como fallidas o parciales las ejecuciones y comandos que ya no tengan trabajo activo, liberar sus leases vencidos y ejecutar la reconciliación con la frecuencia necesaria.
- Mantener las duraciones y categorías de error seguras, sin exponer datos de perfil en el dashboard.

## Capabilities

### New Capabilities

### Modified Capabilities

- `busqueda-por-perfil`: completar todas las búsquedas con trabajo acotado y reanudable, conservando el resultado compartido e idempotente.
- `observabilidad-operativa`: mostrar progreso agregado y cerrar oportunamente ejecuciones de fuente interrumpidas.
- `comandos-administrativos`: finalizar los comandos manuales huérfanos y permitir iniciar otro cuando el anterior ya no tenga trabajo activo.

## Impact

Afecta el despacho y procesamiento Celery en `jobs/tasks.py`, los conectores de fuentes, los modelos y tareas de `operations`, el schedule de Celery Beat y las métricas del dashboard. Debe mantener compatibilidad con la pausa global y con la futura pausa de búsqueda por perfil; no cambia el límite global de 15 minutos ni modifica producción.
