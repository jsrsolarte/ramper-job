# Design

## Context

La vacante compartida puede actualizarse durante una búsqueda y su análisis puede volver a ejecutarse, pero las decisiones de seguimiento pertenecen a cada perfil. El estado de seguimiento ya conserva el estado previo al descarte y permite restaurarlo. Véanse `proposal.md` y las deltas de `ingesta-vacantes` y `dashboard-vacantes`.

## Goals / Non-Goals

**Goals:**
- Mantener el descarte manual ligado al perfil y a la identidad persistente de la vacante.
- Evitar que una reingesta, una nueva revisión del perfil o un análisis nuevo conviertan un seguimiento descartado en recomendación.
- Mantener independientes los estados de perfiles distintos y conservar la restauración explícita existente.

**Non-Goals:**
- Consultar la bolsa para determinar si una publicación sigue abierta, fue cerrada o venció.
- Añadir estados de vigencia de la publicación o cambiar la frecuencia de búsqueda.
- Deduplicar semánticamente publicaciones distintas que tengan URL o identidad diferentes.

## Decisions

### Usar la identidad existente de fuente y URL canónica

Cuando el scraping encuentra una publicación ya registrada, actualiza la misma vacante. La relación de seguimiento por perfil se conserva y se consulta antes de crear una recomendación. Un análisis nuevo puede actualizar el resultado, pero no modifica por sí mismo el estado de seguimiento.

**Alternativa considerada:** crear otra vacante o seguimiento cuando cambia el análisis. Se descarta porque permitiría que la misma publicación vuelva a aparecer y fragmentaría su historial.

### Tratar el descarte como una decisión persistente por perfil

Una vacante en estado descartado permanece fuera de Recomendaciones y sus conteos aunque el scraping actualice sus datos, se genere otra versión de análisis o cambie la revisión del perfil. Solo la acción explícita de restaurar recupera el estado anterior. Los procesos de reingesta y análisis no restauran ni reabren automáticamente ese seguimiento.

**Alternativa considerada:** volver a pendiente al detectar datos o puntajes nuevos. Se descarta porque ignora la decisión explícita de la persona.

### Conservar la independencia entre perfiles

El estado descartado se evalúa en el seguimiento del perfil actual. Una misma vacante puede estar descartada para un perfil y seguir recomendada para otro. No se cambia el registro compartido de la vacante para representar una decisión individual.

### Mantener los seguimientos descartados archivados

El archivado lógico existente no elimina el seguimiento. Si una vacante archivada y descartada se vuelve a encontrar, no se crea otro seguimiento pendiente para ese perfil; la vacante permanece fuera de Recomendaciones hasta que se restaure explícitamente.

## Risks / Trade-offs

- [La identidad de una publicación puede cambiar si cambia su URL] → Aplicar la regla a la identidad de fuente y URL canónica ya usada por la deduplicación; publicaciones con identidad nueva no se consideran automáticamente la misma vacante.
- [Una consulta puede olvidar filtrar estados descartados] → Centralizar o reutilizar el criterio de recomendación y validar también los conteos, la paginación y el reanálisis con pruebas de integración.
- [Una persona podría querer reconsiderar una vacante descartada] → Mantener disponible la acción explícita de restaurar y recuperar el estado previo.

## Migration Plan

1. Revisar el upsert, la asociación de análisis y la transición de seguimiento para encontrar rutas que creen o reactiven una recomendación descartada.
2. Preservar el seguimiento existente para la misma fuente y URL canónica durante la reingesta y el reanálisis; no agregar llamadas a páginas de empleo para consultar disponibilidad.
3. Aplicar el filtro de estados descartados a las recomendaciones y conteos, dejando intactos los estados de otros perfiles y el flujo de restauración.
4. Añadir pruebas de regresión y validar la interfaz y las transiciones con registros existentes.

## Open Questions

Ninguna. Una publicación con identidad diferente se trata como otra vacante; la coincidencia semántica entre publicaciones queda fuera de este cambio.
