# Proposal

## Why

Los estados de seguimiento antiguos hacen crecer indefinidamente las listas y conteos personales. Archivar en forma lógica los seguimientos sin actividad después de 30 días mantiene útil el dashboard sin borrar las vacantes compartidas ni el historial de otros perfiles.

## What Changes

- Ejecutar una tarea diaria que marque como archivados los seguimientos personales que lleven 30 días sin cambiar de estado.
- Aplicar la retención a todos los estados, incluidas recomendaciones pendientes, descartadas y etapas de postulación.
- Excluir los registros archivados de pestañas y conteos, conservando los datos subyacentes y el seguimiento independiente de otros perfiles.
- Restablecer el plazo de 30 días cada vez que el estado cambie.
- Completar la tarea de retención antes de la salida a staging.
- Ejecutar después de `descarte-automatico-recomendaciones` para que las recomendaciones primero pasen a Descartadas y el plazo de 30 días corra desde esa transición.

## Capabilities

### New Capabilities

### Modified Capabilities
- `seguimiento-postulaciones`: archivar lógicamente estados personales que lleven 30 días sin cambiar.
- `dashboard-vacantes`: dejar de mostrar en listas y conteos los seguimientos personales archivados.

## Impact

- Tarea periódica diaria y persistencia de seguimiento por perfil.
- Listas, conteos y retención del historial personal.
- No elimina la vacante compartida ni análisis de otros perfiles; no requiere borrado físico.
- Depende de `fechas-relativas-vacantes` y `descarte-automatico-recomendaciones`; debe implementarse antes de `despliegue-staging-ramper-job`.
