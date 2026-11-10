# Design

## Context

La página de estadísticas ya recibe un periodo común para puntajes y fallos de formato. `OperationalRun` registra cada consulta de fuente con origen, estado, duración y fechas; las ejecuciones terminadas conservan `finished_at`.

## Goals / Non-Goals

**Goals:**
- Reutilizar el periodo seleccionado y los registros operativos existentes.
- Mantener el resumen anónimo y separado del historial por ejecución de Observabilidad.
- Usar un diseño de dos columnas que se apile en pantallas estrechas.

**Non-Goals:**
- Añadir métricas de disponibilidad de publicaciones o de calidad de vacantes.
- Cambiar el scraping, la frecuencia de búsqueda o el modelo de datos.

## Decisions

- Filtrar por `kind=ingestion`, `operation=source_query`, `started_at` dentro del intervalo y `finished_at` presente. Excluir ejecuciones en curso para que no distorsionen volumen, duración o porcentaje.
- Agrupar por fuente y calcular mediana y percentil 95 sobre duraciones registradas. Para el percentil 95 se usará rango más cercano; la mediana promediará los dos valores centrales cuando el volumen sea par.
- Considerar no exitosos los estados parcial, reintento y fallido; calcular el porcentaje sobre todas las ejecuciones terminadas de esa fuente.
- Mover el selector de periodo antes de las tarjetas de seguimiento y rendimiento, manteniendo ese mismo periodo para puntajes y fallos de formato.
- Mantener el seguimiento por perfil y el rendimiento en una cuadrícula de dos columnas en escritorio y una columna en móvil.

## Risks / Trade-offs

- Un volumen inusualmente alto de ejecuciones podría hacer costoso ordenar duraciones en memoria → limitar la consulta estrictamente al periodo seleccionado y solo a `source_query` terminadas.
- Una fuente con pocas ejecuciones puede tener percentiles poco representativos → mostrar también el total de ejecuciones para contextualizar sus tiempos.

## Migration Plan

No requiere migración. El rollback retira la agregación y la tabla, y restaura el selector de periodo a la tarjeta de puntuaciones.
