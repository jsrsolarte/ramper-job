# Design

## Context

Ver `proposal.md` y las especificaciones de `compatibilidad-vacantes`, `preferencias-busqueda-perfil` y `dashboard-vacantes`. Actualmente el modelo produce un puntaje de 0 a 100 y el análisis guarda una referencia a la configuración usada. La nueva escala requiere que los análisis viejos se distingan de los nuevos durante la transición.

## Goals / Non-Goals

**Goals:**

- Aplicar una rúbrica estable, auditable y compartida por perfil y vacante.
- Mantener los puntajes finales enteros y comparables en la escala 0–10.
- Hacer que el umbral de perfil afecte solo la consulta del dashboard.
- Reprocesar análisis vigentes sin perder el historial.

**Non-Goals:**

- Cambiar OmniRoute, el modelo configurado o el servicio proveedor.
- Usar ubicación o modalidad en la puntuación; continúan siendo condiciones de elegibilidad.
- Permitir editar pesos individuales por aspirante en esta entrega.

## Decisions

### Rúbrica fija con puntos por criterio

La configuración de matching incluirá una rúbrica versionada con cinco criterios y límites fijos:

| Criterio | Máximo | Anclas de puntuación |
|---|---:|---|
| Competencias y habilidades requeridas | 4 | 0 sin evidencia o contradicción; 1 evidencia débil o transferible; 2 evidencia parcial y directa; 3 evidencia directa para la mayoría de requisitos; 4 evidencia sólida para las competencias centrales |
| Experiencia y responsabilidades relevantes | 2 | 0 sin evidencia o contradicción; 1 experiencia relacionada o parcial; 2 experiencia directamente pertinente |
| Alineación de cargo o sector | 2 | 0 sin relación o contradicción; 1 cargo o sector adyacente; 2 alineación directa |
| Educación o certificaciones explícitamente requeridas | 1 | 0 no cumple, está contradicho o no hay evidencia; 1 cumple con evidencia; si no hay requisito explícito, 1 con estado `no_aplica` |
| Otros criterios explícitos del perfil, sin ubicación | 1 | 0 no cumple, está contradicho o no hay evidencia; 1 cumple con evidencia; si no hay otro criterio explícito, 1 con estado `no_aplica` |

El modelo devuelve puntos, estado y evidencia para cada criterio, no el total. La aplicación valida límites y criterios requeridos, y suma los puntos para evitar errores aritméticos o totales inconsistentes. Para criterios con puntos graduales, `sin_evidencia` y `contradicho` se distinguen aunque ambos otorguen cero. La evidencia debe ser breve y rastreable al CV o al contenido de la vacante; no se inventan credenciales ni experiencia.

### La ubicación se mantiene como elegibilidad previa

El proceso de búsqueda y elegibilidad existente continúa descartando vacantes incompatibles con ubicaciones y modalidad aceptadas antes de solicitar la evaluación. Así, el modelo no compensa una ubicación no elegible con una puntuación alta ni penaliza dos veces una condición ya filtrada.

### Umbral independiente de la revisión del perfil

El umbral se guarda como preferencia actual del perfil, con valor predeterminado 0. No forma parte de la revisión del CV ni de la entrada al modelo: cambiarlo no debe invalidar análisis, regenerar consultas o crear trabajo de IA. La consulta filtra por el mínimo antes de ordenar y paginar.

### Versionado e historial

Cada análisis nuevo conserva la versión de rúbrica usada mediante la configuración de matching ya asociada, además del desglose y estados/evidencia. Los análisis anteriores se marcan o identifican como escala histórica y no se convierten proporcionalmente de 0–100 a 0–10, porque una conversión aritmética no equivale a una evaluación con la nueva rúbrica.

Tras activar la nueva versión, se encola de forma idempotente el análisis más reciente por combinación vigente de perfil y vacante. Mientras esa nueva evaluación esté pendiente, el dashboard no mezcla ni presenta el puntaje histórico como si estuviera en escala 0–10; solo incluye puntuaciones calculadas con la rúbrica nueva. El análisis anterior se conserva en el historial. Los fallos de IA permanecen reintentables conforme al mecanismo existente.

### Presentación

Las tarjetas muestran el puntaje con denominador `/10`. El desglose se ofrece en una sección secundaria por criterio, con puntos máximos, estado de evidencia y evidencia breve; las razones y los aspectos por revisar siguen en segundo plano para mantener la tarjeta enfocada en los datos de la vacante.

## Risks / Trade-offs

- [Rúbrica fija puede simplificar demasiado vacantes particulares] → Conservar criterios explícitos del perfil en el último punto y evidencia por criterio para inspeccionar el motivo de cada resultado.
- [Una migración por lotes puede tardar o fallar parcialmente] → Encolar por combinación de forma idempotente, permitir reintentos y no ocultar el estado de resultados pendientes.
- [El umbral puede dejar el dashboard sin tarjetas] → Permitir elegir 0 para ver todas las vacantes con resultado vigente.
- [La respuesta del modelo puede omitir o deformar el desglose] → Validar estructura, límites y estados antes de guardar; tratar una respuesta inválida como análisis fallido, no como puntaje cero.

## Migration Plan

1. Añadir campos para desglose, evidencia/estado por criterio y versión identificable de rúbrica; agregar el umbral entero del perfil con valor inicial 0.
2. Publicar la nueva configuración versionada y actualizar el contrato de solicitud/respuesta del modelo.
3. Activar el cálculo del puntaje final en la aplicación y la visualización/filtrado por `/10`.
4. Encolar los análisis vigentes existentes por perfil y vacante, preservando registros anteriores y sus puntajes originales como históricos.
5. Revisar pendientes y fallos mediante el estado y los reintentos ya disponibles.

Rollback: desactivar la nueva configuración y detener el encolado de nuevos reprocesamientos. Mantener los análisis y campos añadidos; no convertir ni borrar puntajes históricos. Para volver a presentar resultados anteriores, restaurar explícitamente su presentación de escala histórica, nunca etiquetarlos como `/10`.

## Open Questions

Ninguna que afecte el comportamiento o la implementación acordada.
