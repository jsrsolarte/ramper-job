# Design

## Context

Las tarjetas muestran hoy el puntaje como número sobre 10. El filtro del dashboard y el mínimo del perfil se eligen mediante opciones accesibles representadas con estrellas. La rúbrica decimal es un cambio independiente y debe integrarse antes de representar sus resultados con estrellas.

## Goals / Non-Goals

**Goals:**
- Representar los puntajes y umbrales como estrellas de 0 a 5.
- Permitir que el filtro temporal del dashboard se ajuste seleccionando opciones de estrellas, sin usar un deslizador.
- Mantener puntajes exactos para consultas, ordenamiento, umbrales y accesibilidad.
- Mantener guardado el mínimo del perfil como entero de 0 a 10.

**Non-Goals:**
- Cambiar la rúbrica, la ponderación de criterios, el rango real del puntaje o el tipo de dato almacenado.
- Convertir los umbrales de perfil o temporales a valores decimales.
- Cambiar cómo se incluyen o excluyen vacantes según el filtro.

## Decisions

- En el perfil, presentar opciones de cero a cinco estrellas. Una estrella representa dos puntos en la escala interna de 0 a 10; conservar valores históricos de media estrella al editar otros campos.
- En el dashboard, presentar opciones accesibles seleccionables como estrellas. La primera opción representa el mínimo persistido en el perfil; las opciones siguientes usan umbrales de estrellas completas mayores que ese mínimo, hasta cinco estrellas. Elegir una opción navega al mismo listado con `score_min`; no requiere botón ni modifica el perfil.
- Representar cada puntaje de análisis con estrellas calculadas a partir del puntaje exacto sobre 10. Si el puntaje decimal no cae en un paso de media estrella, redondear la representación a la media estrella más cercana y resolver los empates hacia arriba. No usar el valor redondeado para consultas, filtrado ni ordenamiento.
- Mantener una etiqueta textual accesible que comunique el puntaje numérico exacto sobre 10 y el equivalente visual. Para los controles, comunicar tanto las estrellas como el umbral numérico y la indicación de “o más”.
- Usar radios nativos para la selección del perfil, con etiquetas visuales de estrellas. En el dashboard, usar enlaces accesibles con etiquetas que anuncien el umbral y el estado seleccionado; las estrellas son la presentación visual de esos enlaces.
- Alternativa considerada: redondear y persistir el análisis a pasos de media estrella. Se descarta porque cambiaría los resultados y la semántica de la rúbrica, aunque el objetivo es únicamente visual.

## Risks / Trade-offs

- Puntajes cercanos pueden verse iguales después del redondeo visual → conservar el valor exacto en la etiqueta accesible y usar siempre la precisión original en el orden y filtro.
- Estilizar un control `range` con estrellas puede variar entre navegadores → mantener su semántica nativa, valor y teclado, y verificar la presentación en los navegadores soportados durante la implementación.

## Migration Plan

- Implementar después de `rubrica-criterios-criticos-decimales` y antes del despliegue a staging.
- No requiere migración de datos. En caso de reversión, restaurar la presentación numérica manteniendo los mismos valores persistidos y reglas de filtrado.
