# Proposal

## Why

La rúbrica calcula en una escala de 0 a 10 y la interfaz la convierte a estrellas, lo que dificulta entender y filtrar las puntuaciones. Una escala común de 0 a 5 en medios puntos hace coincidir el resultado con las estrellas visibles.

## What Changes

- Calcular y guardar el resultado final entre 0 y 5 en incrementos de 0,5, redondeando al medio punto más cercano y los empates hacia arriba.
- Convertir los análisis existentes sin volver a analizarlos, conservando su origen, versión, evidencia y trazabilidad.
- Ofrecer en el perfil únicamente mínimos enteros de 0 a 5 estrellas; convertir los mínimos históricos fraccionarios al entero superior.
- En cada estado de vacantes analizadas ofrecer «Todas» y solo puntuaciones exactas presentes en ese estado, incluidas medias estrellas.
- Adaptar estadísticas, validaciones, deducciones, recomendaciones y versiones a la nueva escala sin cambiar estados de seguimiento por la migración.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `compatibilidad-vacantes`: rúbrica versionada de cinco puntos y conversión trazable sin reanálisis.
- `preferencias-busqueda-perfil`: umbral entero entre cero y cinco estrellas y conversión de mínimos históricos.
- `dashboard-vacantes`: filtros de puntuación exacta disponibles por estado y distribución coherente.
- `estadisticas-plataforma`: estadísticas de puntuaciones coherentes con ambas versiones de escala.

## Impact

Afecta cálculo, validador, prompts, configuración, migraciones, descubrimientos y umbrales, vistas y filtros, estadísticas, pruebas y datos históricos. Requiere una migración compatible con despliegues y reversión; no autoriza cambios de producción ni implica reprocesar CV o llamar a la IA para convertir datos.
