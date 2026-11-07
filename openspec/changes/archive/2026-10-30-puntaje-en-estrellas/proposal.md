# Proposal

## Why

La escala de 0 a 10 es menos rápida de interpretar visualmente y dificulta ajustar el umbral con una interacción simple. Representar puntajes y umbrales como estrellas mantiene la escala conocida y permite comparar oportunidades de un vistazo.

## What Changes

- Mostrar el puntaje de compatibilidad de cada vacante como una valoración de 0 a 5 estrellas, en pasos de media estrella.
- Representar con el mismo control de estrellas el mínimo temporal del dashboard y el mínimo persistente del perfil.
- Mantener los valores de filtros y perfil como enteros de 0 a 10; cada punto equivale a media estrella y los filtros incluyen puntajes iguales o superiores al mínimo.
- Conservar el puntaje exacto para accesibilidad, ordenamiento y filtrado; para puntajes decimales, redondear solo su representación visual a la media estrella más cercana.
- Mantener sin cambios la rúbrica, los resultados almacenados y el criterio numérico de compatibilidad.
- Completar esta funcionalidad después de la rúbrica decimal y antes del despliegue a staging.

## Capabilities

### New Capabilities

### Modified Capabilities
- `dashboard-vacantes`: presentar los puntajes y el filtro temporal mediante estrellas sin alterar el filtrado ni el orden numérico.
- `preferencias-busqueda-perfil`: presentar y ajustar con estrellas el mínimo persistente, conservando su valor entero de 0 a 10.

## Impact

- Interfaz de tarjetas y controles de puntaje del dashboard y del formulario de perfil.
- Conversión visual entre puntajes de 0 a 10 y estrellas de 0 a 5, con medias estrellas.
- Accesibilidad del control y del puntaje mostrado; filtrado y ordenamiento conservan la precisión numérica existente.
- Depende de `rubrica-criterios-criticos-decimales` para mostrar puntajes con decimales y debe completarse antes de `despliegue-staging-ramper-job`.
