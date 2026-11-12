# Proposal

## Why

Ramper Job consulta El Empleo y puede ampliar las oportunidades encontradas para cada perfil incorporando Computrabajo Colombia. Una búsqueda pública con el filtro de recencia y el orden acordados devolvió HTML con tarjetas de vacantes en la prueba realizada por el usuario.

## What Changes

- Incorporar Computrabajo Colombia al registro de conectores y al flujo habitual de búsquedas por perfil.
- Construir la ruta pública por término y, cuando esté disponible, ciudad, y consultar solo la primera página con `pubdate=1`, `p=1` y `by=relevance`.
- Configurar el User-Agent de Computrabajo, usando inicialmente el valor de Chrome de la prueba compartida.
- Extraer y normalizar los datos disponibles del listado y las fichas públicas, conservando identidad, fuente y enlace.
- Informar la indisponibilidad y detener las consultas restantes a Computrabajo en la ejecución ante bloqueos, manteniendo aisladas las demás fuentes.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `ingesta-vacantes`: añadir la extracción y normalización de vacantes públicas de Computrabajo.
- `busqueda-por-perfil`: consultar Computrabajo con términos, ubicaciones y límites acordados.

## Impact

Afecta conectores, registro de fuentes, configuración y pruebas de ingesta. Se reutilizan deduplicación, elegibilidad, análisis y observabilidad existentes. La alta administrativa mediante URL de Computrabajo y la paginación adicional quedan fuera del alcance.
