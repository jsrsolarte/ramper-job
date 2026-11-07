# Design

## Context

Recomendaciones equivale al estado pendiente de decisión del seguimiento por perfil. En la implementación actual puede no existir aún una fila explícita de seguimiento para ese estado. La spec `fechas-relativas-vacantes` añade una fecha de finalización de análisis y una marca de entrada al estado actual.

## Goals / Non-Goals

**Goals:**
- Descartar diariamente solo recomendaciones vigentes y todavía pendientes para cada perfil.
- Registrar el descarte como transición de estado normal para actualizar fechas, listados y conteos.
- Reiniciar el plazo al restaurar una recomendación descartada automáticamente.

**Non-Goals:**
- Eliminar vacantes o resultados de análisis.
- Descartar vacantes que ya avanzaron, fueron descartadas manualmente o dejaron de ser recomendaciones vigentes.
- Aplicar el plazo a la fecha de publicación de la fuente.

## Decisions

- Depender de `fechas-relativas-vacantes` y medir los siete días desde la entrada al estado pendiente; para una recomendación nueva coincide con la finalización de su análisis vigente. La fecha de publicación no es adecuada porque mide antigüedad de la vacante, no cuánto lleva en la bandeja del perfil.
- Enlazar una recomendación vigente con su análisis completado actual y verificar que siga pendiente antes de descartarla. Esto evita actuar sobre una versión superada o sobre vacantes que la persona ya avanzó.
- Usar la transición existente a Descartadas, guardar Pendiente como estado previo y registrar la hora actual como inicio del estado descartado. La restauración crea una nueva entrada a Recomendaciones y reinicia los siete días.
- Ejecutar el proceso una vez al día mediante el scheduler de la aplicación. El filtro de estado y plazo hace la operación idempotente y permite recuperar ejecuciones omitidas.
- Alternativa considerada: eliminar una recomendación por antigüedad desde su publicación. Se descarta porque una publicación antigua puede haberse incorporado recientemente a la búsqueda de un perfil.

## Risks / Trade-offs

- Una tarea diaria puede descartar hasta un día después de cumplir el plazo → definir el criterio como “siete días o más” y ejecutar a una hora diaria estable.
- Una revisión de perfil puede cambiar la vigencia del análisis → seleccionar solo la evaluación vigente al momento de la ejecución.

## Migration Plan

- Implementar después de `fechas-relativas-vacantes`; no se necesita reanalizar ni borrar datos existentes.
- Si se desactiva la tarea, los estados ya descartados permanecen y pueden restaurarse desde el dashboard.
