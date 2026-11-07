# Design

## Context

La vista de vacantes ya filtra y ordena los resultados por perfil y estado antes de paginarlos. Ver `proposal.md` y la spec del dashboard para el alcance funcional.

## Goals / Non-Goals

- Permitir saltos directos manteniendo el estado y los parámetros de consulta existentes.
- Conservar la paginación del servidor y sus controles anterior y siguiente.
- No cambiar los datos, los criterios de selección ni las reglas de ordenamiento.

## Decisions

### Paginación compacta en el servidor

La vista usa `Paginator` de Django y `get_elided_page_range` para calcular páginas cercanas, extremos y omisiones. Se eligió esta función frente a una implementación manual para mantener el comportamiento de límites y páginas inválidas de Django.

### Enlaces con el contexto actual

La vista copia los parámetros de consulta, reemplaza únicamente `page` y construye los enlaces numerados y direccionales. La plantilla marca la página actual con `aria-current` y oculta las elipsis a lectores de pantalla.

## Risks / Trade-offs

- [Las listas extensas tienen rangos distintos según la página] → Comprobar inicio, mitad y final con varias páginas y filtros activos.
- [Un filtro podría perderse al navegar] → Construir cada enlace desde una copia de los parámetros existentes.

## Migration Plan

No hay migración de datos. La reversión consiste en restaurar la navegación anterior de la vista y la plantilla.
