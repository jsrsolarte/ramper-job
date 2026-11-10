# Design

## Context

La consulta individual de una fuente ya crea registros operativos con fecha, fuente, estado, vacantes encontradas, duración y categoría/resumen seguro de error. El tablero actual usa esos registros para métricas agregadas y errores recientes, pero no ofrece una lista cronológica completa. Ver `proposal.md` para la motivación y `specs/observabilidad-operativa/spec.md` para el contrato.

## Goals / Non-Goals

**Goals:**
- Reutilizar el historial operativo existente para listar consultas de fuente dentro del periodo elegido.
- Permitir recorrer el historial de forma acotada y mantener el periodo entre páginas.
- Mantener el acceso administrativo y las reglas actuales de privacidad.

**Non-Goals:**
- Consultar Elempleo para determinar si una publicación fue cerrada.
- Cambiar el scheduler, el intervalo, los conectores o el flujo de búsqueda.
- Relacionar una consulta con el contenido del CV, las frases privadas o perfiles individuales.

## Decisions

- Filtrar los registros de tipo `ingestion` de operación `source_query` por el mismo intervalo seleccionado para las métricas y ordenarlos de más reciente a más antiguo. Así se muestran las búsquedas automáticas y cualquier consulta manual que haya llegado al mismo flujo.
- Paginar la lista con un límite fijo de 50 filas por página y conservar `period` en los enlaces. Se evita cargar historial completo sin separar la experiencia de la selección de periodo que ya existe.
- Presentar solo campos operativos existentes y seguros: fecha, fuente, estado, cantidad, duración y resumen/categoría segura del error. No mostrar payload, perfil, vacante ni argumentos de la consulta.

## Risks / Trade-offs

- Una ejecución por perfil puede producir varias filas para la misma fuente y hora aproximada → conservar cada registro; la lista representa intentos reales, no agrupa consultas diferentes.
- En periodos con muchas ejecuciones se requieren varias páginas → mostrar controles de paginación y un estado vacío claro.

## Migration Plan

No requiere migración de datos ni cambios en la ejecución de tareas. El rollback consiste en retirar la lista y la consulta paginada, conservando el historial operativo existente.
