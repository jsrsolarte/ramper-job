# Design

## Context

El flujo actual valida la ubicación antes de llamar a OmniRoute y luego envía CV y publicación en una llamada que devuelve puntaje y contenido organizado juntos. `VacancyAnalysis` tiene un estado general y guarda ambos resultados, mientras el dashboard consulta solo análisis completos. El filtro temporal del dashboard no es el mínimo persistido del perfil y no debe disparar enriquecimiento.

## Goals / Non-Goals

**Goals:**
- Separar la disponibilidad del puntaje de la del contenido organizado.
- Evitar incluir el CV en la llamada de organización.
- Reutilizar la organización entre perfiles para la misma vacante y versión de configuración.
- Conservar mediciones de cada llamada para comparar duración y consumo por etapa.

**Non-Goals:**
- Cambiar la rúbrica, los criterios de elegibilidad geográfica o los mínimos del perfil.
- Usar el filtro temporal del dashboard para decidir qué llamadas de IA ejecutar.
- Añadir una vista administrativa nueva en este cambio; sus registros alimentarán las métricas operativas existentes.

## Decisions

### Mantener la puntuación por perfil y desacoplarla de la organización

La llamada de puntuación seguirá usando CV, preferencias y datos de la publicación; su respuesta ya no incluirá `organized_description`. Cuando la validación del puntaje termine, el análisis de perfil se considera puntuado y el resultado puede consultarse aunque la organización no exista todavía. El control previo de ubicación permanece antes de ambas etapas.

**Alternativa considerada:** una llamada única con respuesta condicional. Se descarta porque todavía procesa el CV y la publicación en conjunto, no permite devolver el puntaje mientras la organización continúa y dificulta medir cada etapa por separado.

### Ejecutar la organización por encima del mínimo persistido del perfil

La decisión se toma usando `Profile.min_score` vigente, tanto al terminar la puntuación como al guardar una reducción del mínimo. Si el puntaje queda por debajo, se conserva como puntuado y se marca la organización como diferida. Al bajar el mínimo, se encolan los resultados que pasan a ser elegibles y aún no tienen organización disponible. El filtro temporal del dashboard solo cambia lo que se muestra.

### Compartir organización por vacante y configuración

Crear un registro de organización reutilizable, con unicidad por vacante y configuración de análisis. La tarea de organización recibe solo los datos de la publicación y el prompt de organización versionado; no recibe CV, preferencias ni datos del perfil. Solicitudes concurrentes encuentran el mismo registro y no crean llamadas duplicadas. Una nueva configuración produce una organización distinta y conserva la anterior para trazabilidad.

Las organizaciones fallidas se pueden reintentar sin invalidar puntajes. Cuando una organización compartida se completa, queda disponible para los análisis relacionados con esa vacante y configuración.

### Separar estados y conservar intentos medibles

El estado existente de `VacancyAnalysis` describe la etapa de puntuación. Un estado adicional por análisis indica si la organización está diferida, pendiente, disponible o agotó sus reintentos. El registro compartido de organización mantiene su propio ciclo pendiente/completo/fallido. La base local se limpiará antes de aplicar los cambios: se eliminan vacantes y datos dependientes, no cuentas, perfiles ni configuración. No se implementará conversión de análisis anteriores al nuevo esquema.

Registrar cada llamada como un intento con etapa, inicio/fin, resultado y tokens de entrada/salida cuando el proveedor los informe. Los campos de tokens serán nulos si no hay datos; no se estimarán ni se guardarán como cero. Los intentos no guardan prompts, CV, texto de perfil ni respuesta completa. La agregación para administración puede integrarse en el panel operativo ya propuesto.

## Risks / Trade-offs

- [La mayoría de vacantes puede superar el mínimo y generar una segunda llamada] → Registrar tasa de elegibilidad, tokens y duración por etapa para medir el resultado real.
- [Cambios simultáneos de umbral o tareas repetidas pueden generar duplicados] → Aplicar unicidad en la organización por vacante/configuración y hacer idempotente la programación por perfil.
- [Una llamada compartida fallida afecta a varios análisis] → Mantener estado y reintentos en el registro compartido; el puntaje continúa disponible para cada perfil.
- [Una publicación puede cambiar conservando su identificador] → Incluir una huella del contenido relevante de la publicación en la identidad de la organización, o invalidar la organización al actualizar esos datos, para no servir contenido obsoleto.
- [El proveedor puede omitir métricas de tokens] → Guardar duración y resultado, y mostrar tokens como no disponibles.

## Migration Plan

1. Limpiar la base local de vacantes y de los análisis, seguimientos y registros de llamadas que dependan de ellas; conservar cuentas, perfiles y configuración.
2. Añadir estados y almacenamiento de organizaciones e intentos de llamada sin backfill de análisis anteriores.
3. Desplegar puntuación y organización en tareas separadas; primero puntuar y luego encolar solo resultados elegibles.
4. Activar el reencolado al reducir el mínimo del perfil y revisar métricas por etapa desde el historial de instrumentación.

Si el cambio se revierte, se puede restaurar la tarea combinada manteniendo los campos nuevos. Los datos locales eliminados no se restauran automáticamente; no se borrarán resultados creados con el flujo nuevo durante un rollback.
