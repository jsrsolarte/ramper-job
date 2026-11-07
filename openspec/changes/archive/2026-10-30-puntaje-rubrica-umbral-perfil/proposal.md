# Proposal

## Why

Los puntajes actuales van de 0 a 100 y el modelo los asigna sin una rúbrica explícita, lo que dificulta comparar resultados. Una escala común de 0 a 10, con criterios ponderados y evidencia registrada, hará las evaluaciones más consistentes y permitirá que cada perfil oculte vacantes por debajo de un mínimo elegido.

## What Changes

- **BREAKING** Cambiar el puntaje de compatibilidad a una escala entera de 0 a 10.
- Enviar al modelo una rúbrica compartida y versionada, con puntajes por criterio y evidencia de apoyo; la aplicación sumará los criterios y calculará el puntaje final.
- Registrar el desglose, el estado de evidencia y la versión de la rúbrica usada en cada análisis.
- Permitir que cada persona elija en su perfil un puntaje mínimo de 0 a 10; aplicar el filtro en el dashboard sin volver a analizar las vacantes.
- Reanalizar en segundo plano los resultados vigentes con la rúbrica nueva, conservando los análisis anteriores para consulta y trazabilidad.
- Excluir la ubicación del puntaje porque ya se valida como condición de elegibilidad antes del análisis.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `compatibilidad-vacantes`: puntaje 0–10, desglose reproducible, evidencia y versión de rúbrica.
- `preferencias-busqueda-perfil`: puntaje mínimo seleccionable por perfil.
- `dashboard-vacantes`: filtrado por el puntaje mínimo del perfil antes de ordenar y paginar resultados.

## Impact

- Configuración versionada de análisis, solicitud y validación de respuestas del modelo, persistencia de análisis y tareas de reprocesamiento.
- Modelo y formulario del perfil, consulta del dashboard y presentación del puntaje.
- Sin nuevas dependencias ni cambios en el proveedor de IA configurado por OmniRoute.
