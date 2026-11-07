# Design

## Context

El dashboard agrega pestañas por estado personal. La rúbrica admite puntajes decimales; la vista «Por analizar» contiene publicaciones que todavía no tienen puntaje. `fechas-relativas-vacantes` proporciona el instante en que cada seguimiento entró a su estado actual.

## Goals / Non-Goals

**Goals:**
- Priorizar por puntaje numérico descendente en Recomendaciones.
- Priorizar por antigüedad del estado, más reciente primero, en cada pestaña de seguimiento.
- Mantener separadas la pertenencia al estado, los conteos y la ordenación de filas.

**Non-Goals:**
- Cambiar el mínimo del perfil o el filtro temporal del dashboard.
- Ocultar vacantes de seguimiento por estar bajo el mínimo de recomendaciones.
- Ordenar «Por analizar» por una puntuación que aún no existe.

## Decisions

Filtrar primero por perfil, revisión vigente y estado de la pestaña. Después, ordenar Recomendaciones por puntaje numérico descendente y las demás etapas de seguimiento por su fecha de entrada al estado, de más reciente a más antigua. El filtro mínimo sigue limitando Recomendaciones; las pestañas de seguimiento conservan todos los elementos de su estado, sin aplicarles el mínimo. Los conteos siguen representando el total de vacantes únicas del estado, sin depender del orden.

Se reutiliza el orden descendente ya establecido para recomendaciones y la marca de tiempo del estado definida en `fechas-relativas-vacantes`. No se añade un control seleccionable: cada pestaña tiene un orden predeterminado acorde a su objetivo. «Por analizar» conserva su orden de cola actual.

## Risks / Trade-offs

- [Los empates de puntaje o timestamps pueden producir un orden inestable] → Añadir un desempate determinista sin cambiar la prioridad principal.
- [No todos los registros históricos pueden tener una fecha de etapa confiable] → Usar la fecha disponible más precisa y aplicar un desempate determinista a los registros sin fecha.
- [Aplicar el mínimo del perfil a todos los estados ocultaría decisiones pasadas] → Mantener el mínimo solo en Recomendaciones y ordenar sin filtrar las pestañas de seguimiento.

## Migration Plan

Depende de la fecha de entrada al estado de `fechas-relativas-vacantes`. Integrar la ordenación específica de cada pestaña antes de stage; no cambia puntajes, filtros ni estados guardados.
