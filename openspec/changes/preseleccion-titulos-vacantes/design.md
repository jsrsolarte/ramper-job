# Design

## Context

Ver `proposal.md` para la motivación y `specs/ingesta-vacantes/spec.md` para el contrato. `ElempleoConnector.fetch` obtiene la lista y consulta la ficha detallada de cada resultado antes de devolverla. Tanto la actualización compartida como la actualización de un perfil usan ese método; por eso el filtro debe insertarse entre la lectura de títulos y la consulta de fichas, en un flujo común. Las búsquedas equivalentes ya se agrupan por términos, ubicación, modalidad, fuente y configuración.

## Goals / Non-Goals

**Goals:**

- Clasificar títulos en lotes antes de consultar descripciones completas.
- Reutilizar una única decisión para perfiles que comparten una solicitud de búsqueda equivalente.
- Preferir conservar una vacante ante cualquier duda o fallo del clasificador.
- Mantener el flujo de análisis por perfil y la extracción manual de URL existentes.
- Exponer un embudo por consulta que continúe actualizándose mientras se completan los análisis asíncronos.
- Mostrar las duraciones operativas en minutos y conservar únicamente métricas agregadas, sin contenido de CV o vacantes.

**Non-Goals:**

- Reemplazar el puntaje detallado de compatibilidad o cambiar la rúbrica.
- Usar el título para descartar por ubicación, modalidad, salario, requisitos o atributos personales.
- Enviar CV, nombres de usuario o datos de contacto a la etapa de preselección.
- Filtrar vacantes que la administración registra directamente por URL.

## Decisions

### Separar descubrimiento de fichas y extracción detallada

Dividir el conector de búsqueda en dos fases: leer resultados de listado con título y URL, y consultar detalles de las fichas seleccionadas. El flujo compartido y el de actualización individual usan el mismo coordinador para ejecutar ambas fases. Los conectores que no puedan separar estas operaciones conservarán el comportamiento previo hasta que implementen la interfaz por fases.

Alternativa considerada: filtrar después de que `fetch` devuelve todos los detalles. Se descarta porque no ahorraría las consultas de ficha que motivan el cambio.

### Clasificar por solicitud de búsqueda equivalente

Enviar a OmniRoute un lote acotado con identificadores opacos, títulos y los términos efectivos compartidos por el grupo de búsqueda. No enviar descripciones, CV ni datos personales. Solicitar una decisión binaria por título: conservar o descartar como claramente ajeno. Los títulos son datos no confiables y se presentan como contenido, no instrucciones.

Los perfiles agrupados tienen criterios efectivos de búsqueda equivalentes, por lo que la decisión del lote se puede aplicar una vez a sus miembros. Las solicitudes diferentes se clasifican en lotes separados para evitar mezclar sus preferencias.

Alternativa considerada: enviar todos los CV de perfiles activos y comparar cada vacante con ellos. Se descarta porque multiplica tokens y mezcla información personal sin aportar valor al filtro por título.

### Aplicar una regla conservadora de conservación

Conservar cuando el modelo identifica compatibilidad, duda, falta contexto o no devuelve una respuesta válida para un título. Si la llamada completa falla, conservar todos los títulos del lote y seguir con extracción y análisis normales. Solo una decisión válida de incompatibilidad clara evita la ficha detallada.

La salida se valida contra los identificadores del lote. Identificadores duplicados, desconocidos o faltantes no pueden causar descarte; cualquier vacante sin decisión válida se conserva.

### No persistir un descarte como decisión laboral

La preselección solo evita el trabajo detallado de esa ejecución. No crea análisis ni seguimiento para una vacante descartada por título; el conector puede evaluarla nuevamente en otra búsqueda. La deduplicación, elegibilidad geográfica y evaluación final se mantienen para los títulos conservados.

### Relacionar el embudo con el resultado asíncrono

La ejecución de consulta conserva conteos agregados de títulos recibidos, conservados, descartados, fichas solicitadas/recibidas, tokens y duración de etapas. Los análisis encolados registran una relación con la consulta de origen; el panel deriva desde esa relación los conteos pendientes, completados, fallidos, conservados por umbral y descartados por puntaje. No se persisten títulos ni contenido de perfil para construir las métricas.

Las duraciones se conservan en milisegundos para cálculo y compatibilidad interna, pero toda la interfaz las presenta en minutos con un decimal.

## Risks / Trade-offs

- [El modelo puede descartar un cargo atípico pero compatible] → Usar una regla de descarte solo para incompatibilidad clara y pasar títulos ambiguos al análisis normal.
- [Una salida parcial o malformada puede perder resultados] → Validar identificadores y conservar toda entrada sin decisión válida.
- [La llamada de preselección puede fallar o añadir demora] → Procesar títulos por lotes y ante fallo abrir el flujo para todas las vacantes del lote.
- [Un filtro conserva demasiadas vacantes y ahorra poco] → Medir proporción de descarte, tokens de entrada y demora en una muestra representativa antes de ajustar el criterio.

## Migration Plan

No requiere migrar datos. Tras desplegar el flujo por fases, las búsquedas automáticas comienzan a clasificar resultados antes de extraer fichas. El registro manual por URL continúa por su camino actual. La reversión desactiva la preselección y consulta todas las fichas como antes, sin cambios en vacantes o análisis existentes.
