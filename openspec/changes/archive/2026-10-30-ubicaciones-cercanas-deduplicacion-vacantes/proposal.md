# Proposal

## Why

Las preferencias actuales muestran frases y ubicaciones como etiquetas y solo comparan las ubicaciones tal como fueron escritas. Además, la misma vacante de Elempleo puede aparecer en más de una búsqueda con otra URL y terminar repetida en el dashboard.

## What Changes

- Presentar las frases de búsqueda y ubicaciones como listas verticales editables.
- Expandir ubicaciones principales a municipios cercanos conocidos para la búsqueda y el análisis de compatibilidad.
- Combinar cada frase con cada ubicación expandida y priorizar publicaciones recientes usando el filtro disponible en Elempleo.
- Reconocer vacantes repetidas de Elempleo por identificador estable y, cuando falte, por una huella normalizada de sus datos.
- Conservar un solo registro visible por vacante sin perder análisis existentes.

## Capabilities

### New Capabilities

- `preferencias-busqueda`: administrar listas editables y considerar áreas metropolitanas cercanas al comparar vacantes.
- `deduplicacion-vacantes`: reconocer y consolidar vacantes repetidas dentro de una misma bolsa.

### Modified Capabilities

## Impact

Formulario y estilos del perfil, expansión de ubicaciones usada en búsquedas y análisis, conector y persistencia de Elempleo, modelo de vacantes y migración de datos para registros existentes.
