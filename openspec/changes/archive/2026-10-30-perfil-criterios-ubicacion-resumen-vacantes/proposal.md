# Proposal

## Why

Los perfiles deben expresar sus preferencias de búsqueda de forma sencilla y explícita. Hoy se guardan como un bloque de texto, no existe una preferencia estructurada de ubicación o trabajo remoto y las descripciones organizadas por IA son demasiado extensas para comparar oportunidades rápidamente.

## What Changes

- Reemplazar los criterios de texto libre por frases individuales que el usuario puede agregar y quitar.
- Permitir varias ubicaciones y señalar si acepta oportunidades remotas.
- Hacer que la IA complemente las frases elegidas con términos respaldados por la hoja de vida y use las preferencias de ubicación al evaluar compatibilidad.
- Presentar cada vacante con un resumen breve y secciones estructuradas para responsabilidades, requisitos y condiciones.
- Asegurar que la descarga de la hoja de vida use una ruta autenticada ligada al perfil propietario.

## Capabilities

### New Capabilities

- `preferencias-busqueda-perfil`: preferencias editables de cargos, ubicaciones y modalidad remota, persistidas por revisión y usadas en búsquedas/análisis.
- `presentacion-vacantes`: descripción organizada, breve y estructurada para mostrar cada vacante junto con su compatibilidad.

### Modified Capabilities

## Impact

- Modelos, formularios, vistas, plantillas y migraciones de perfiles y análisis.
- Generación de términos y análisis estructurados a través del cliente OmniRoute existente.
- Tarjetas del dashboard y descarga privada de CV; no se incorporan dependencias externas.
