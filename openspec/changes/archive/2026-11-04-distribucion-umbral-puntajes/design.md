# Design

## Context

El dashboard limita su lista por el mínimo entero del perfil y ofrece un filtro temporal que solo puede estrecharla. La consulta de la métrica debe usar la misma población de resultados vigentes, pero calcularse antes de aplicar esos umbrales. La nueva rúbrica prevista permitirá puntajes decimales.

## Goals / Non-Goals

**Goals:**

- Mostrar conteos en bandas de un punto usando análisis completados de la revisión y versión vigentes.
- Calcular una mediana reproducible y comunicar el efecto esperado del umbral recomendado.
- Mantener el límite del perfil y el filtro temporal como valores enteros.

**Non-Goals:**

- Cambiar la rúbrica ni reanalizar vacantes.
- Guardar el umbral recomendado de forma automática.
- Mostrar recomendaciones con menos de cinco resultados.

## Decisions

- Calcular la distribución desde todos los análisis vigentes elegibles del perfil antes de filtrar por `profile.min_score` o `score_min`. Esto deja visible la población que el usuario podría recuperar cambiando el mínimo.
- Presentar la distribución debajo del listado de vacantes y su paginación, de modo que el panel de métricas no desplace las oportunidades fuera del foco inicial.
- Agrupar puntajes decimales en bandas semiabiertas `[0,1)`, `[1,2)` ... `[9,10]`; el extremo 10 se incluye en la última banda.
- Para cinco o más resultados, obtener la mediana exacta, redondearla al entero más cercano con empates hacia arriba y contar cuántos resultados alcanzarían el umbral. La mediana es menos sensible a unos pocos puntajes extremos que la media y la explicación se puede mostrar al usuario.
- La acción de aplicar la recomendación actualiza solo el filtro temporal cuando el valor recomendado es igual o superior al mínimo del perfil. Si es menor, la interfaz enlaza a la edición del perfil, cuya preferencia solo cambia cuando la persona la guarda.

## Risks / Trade-offs

- **La recomendación varía con muestras pequeñas** → No recomendar con menos de cinco resultados y mostrar el tamaño de muestra junto a la sugerencia.
- **Una nueva versión de rúbrica cambia la distribución** → Excluir resultados históricos de versiones distintas y mostrar solo análisis vigentes.
- **Una sugerencia inferior al mínimo del perfil no cambia el listado de inmediato** → Explicar la restricción y ofrecer acceso a la configuración persistente.
