# Design

## Context

El seguimiento se almacena por perfil y vacante. La vacante y el análisis son recursos compartidos o independientes del seguimiento. Los cambios de estado ya actualizan una marca de tiempo; la spec `fechas-relativas-vacantes` define una marca explícita de entrada al estado actual, que también es necesaria para calcular la retención.

## Goals / Non-Goals

**Goals:**
- Ejecutar diariamente un archivado lógico idempotente de estados inactivos por perfil.
- Excluir los registros archivados de listados y conteos activos.
- Conservar la vacante compartida, análisis y seguimiento de otros perfiles.

**Non-Goals:**
- Borrar físicamente vacantes o análisis.
- Crear un servicio independiente de tareas periódicas.
- Hacer que el perfil actualice el temporizador al editar datos que no cambian el estado.

## Decisions

- Depender de `fechas-relativas-vacantes` para obtener la fecha de entrada al estado actual. Para recomendaciones pendientes sin un estado explícito, usar la finalización del análisis vigente como inicio; el job de 7 días de descarte puede moverlas a descartadas y reiniciar el plazo.
- Marcar el seguimiento del perfil como archivado mediante un borrado lógico, separado de su fecha de cambio de estado. Así se conserva el estado y la vacante para auditoría, y no se afecta a otros perfiles.
- Ejecutar una tarea periódica una vez al día en la zona horaria de la aplicación y seleccionar únicamente seguimientos activos cuyo estado lleve al menos 30 días sin cambios.
- Hacer la operación idempotente y limitarla a las relaciones de seguimiento del perfil. La reejecución no debe tocar una relación ya archivada ni eliminar datos compartidos.
- Alternativa considerada: eliminar la fila de seguimiento. Se descarta porque perdería la distinción entre nunca seguida y archivada, y podría reactivar recomendaciones al recalcular conteos.

## Risks / Trade-offs

- La tarea de siete días puede cambiar el estado y reiniciar el reloj de 30 días → usar una marca explícita de estado y cubrir la interacción entre ambas tareas.
- Registros históricos sin fecha de transición fiable podrían archivarse en un momento incorrecto → usar la marca de tiempo disponible más confiable o dejarlos fuera hasta que tengan una referencia verificable.

## Migration Plan

- Depende de `fechas-relativas-vacantes` para contar correctamente el tiempo en estado.
- Añadir el marcador de archivado de forma nullable/inactiva para preservar los seguimientos actuales durante la migración.
- Reversión: desactivar la tarea y restaurar los marcadores de archivado; los datos subyacentes siguen presentes.
