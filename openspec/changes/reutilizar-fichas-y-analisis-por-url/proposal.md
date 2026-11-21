# Proposal

## Why

Las mismas publicaciones aparecen en numerosas búsquedas y sus fichas vuelven a descargarse. Los análisis existentes también pueden repetirse al cambiar el perfil o la configuración, lo que consume tiempo y tokens.

## What Changes

- Identificar por fuente y URL pública normalizada, sin parámetros ni fragmento, las fichas previamente descargadas antes de consultar detalles; reutilizar sus datos.
- Descargar las fichas nuevas o sin evidencia confiable de detalle y preservar la recuperación ante fallos.
- Conservar el análisis completado por vacante y perfil sin reevaluarlo por cambios de perfil, configuración, contenido o registro manual; analizar con el perfil vigente solo cuando no exista resultado completado.
- Distinguir en observabilidad fichas reutilizadas de solicitudes reales y conservar visibilidad de análisis históricos.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `ingesta-vacantes`: consulta de fichas nuevas y reutilización de fichas conocidas.
- `deduplicacion-vacantes`: identidad de publicación basada en URL normalizada por fuente.
- `compatibilidad-vacantes`: preservación del análisis completado por perfil sin reanálisis.
- `busqueda-por-perfil`: reutilización entre búsquedas y revisiones de perfil.
- `recuperacion-trabajos-analisis`: recuperación de pendientes sin reemplazar resultados completados.
- `dashboard-vacantes`: conservar accesibles resultados de revisiones anteriores.
- `observabilidad-operativa`: métricas separadas de consultas y reutilización.

## Impact

Afecta conectores, trabajo durable de ingesta, identidad y migración de datos, planificación y visualización de análisis y métricas. No incluye refresco automático de fichas conocidas: cambios o cierres posteriores pueden no reflejarse. No incluye promoción productiva.
