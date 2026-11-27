# Design

## Context

La distribución administrativa se construye en `operations.platform_statistics` con diez intervalos sobre los puntajes originales de 0 a 10 y una mediana decimal. La plantilla `operations/templates/operations/platform_statistics.html` presenta sus etiquetas y mediana directamente. La escala visual de vacantes y filtros ya define cinco estrellas como equivalentes a diez puntos.

## Goals / Non-Goals

**Goals:**
- Mostrar las etiquetas de los diez intervalos en rangos consecutivos de media estrella.
- Mostrar la mediana convertida a estrellas y mantener la muestra y las separaciones por rúbrica.
- Conservar los puntajes de origen y sus conteos actuales.

**Non-Goals:**
- Modificar la rúbrica, el puntaje almacenado, la recomendación o los filtros de perfil.
- Cambiar la distribución privada de la pantalla «Análisis» del aspirante.
- Redondear cada puntaje al equivalente visual de media estrella antes de calcular la distribución.

## Decisions

- Aplicar la conversión lineal `estrellas = puntaje / 2` a la representación de los intervalos y la mediana. Una estrella corresponde a dos puntos de la escala interna.
- Mantener los diez intervalos existentes y dividir sus límites entre dos para mostrarlos como `0–<0,5`, `0,5–<1`, …, `4,5–5` estrellas. Esta opción preserva conteos y evita que el cambio visual altere la distribución estadística.
- Convertir la mediana exacta ya calculada y mostrarla con hasta dos decimales de estrella. La conversión y el formato son de presentación; los datos de origen no se modifican.
- Conservar las proporciones de las barras, el tamaño de muestra, el periodo y la separación por versión de rúbrica. Cambiar únicamente unidades y etiquetas visibles.

## Risks / Trade-offs

- [Los intervalos en media estrella podrían confundirse con categorías redondeadas de estrellas de las tarjetas] → Etiquetarlos como rangos con límites inclusivos/exclusivos y documentar que se convierten desde los intervalos exactos originales.
- [Una mediana con dos decimales podría no ser representable con iconos de media estrella] → Mostrar la mediana como valor numérico en estrellas (por ejemplo, `3,13 estrellas`) y mantener el gráfico por rangos.

## Migration Plan

- No requiere cambios de datos ni migración. El puntaje original de 0 a 10 sigue siendo la fuente de cálculo.
- Si se revierte la presentación, volver a mostrar los mismos conteos y mediana en la escala original; no requiere revertir datos.
