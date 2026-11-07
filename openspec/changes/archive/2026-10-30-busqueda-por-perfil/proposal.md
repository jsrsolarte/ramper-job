# Proposal

## Why

La consulta actual de Elempleo revisa una lista general y no usa los criterios ni la hoja de vida de cada familiar para encontrar vacantes. Las búsquedas específicas de Elempleo, como la ruta por “procesos” compartida por el usuario, permiten enfocar la recolección antes de analizar compatibilidad.

## What Changes

- Derivar con IA palabras clave laborales desde el CV y los criterios vigentes de cada perfil.
- Consultar Elempleo con búsquedas específicas por palabra clave, en lugar de depender solo de la lista general.
- Reutilizar y deduplicar vacantes encontradas para más de un perfil, conservando el análisis privado de cada cuenta.
- Permitir al administrador ajustar el prompt de generación de palabras clave dentro de la configuración versionada existente.
- Mantener la URL original y la explicación organizada por IA en los resultados.

## Capabilities

### New Capabilities
- `busqueda-por-perfil`: generación de palabras clave y consulta de fuentes de empleo a partir de cada perfil.

### Modified Capabilities

## Impact

- Perfiles y versiones de perfil, configuración versionada de IA, conectores de vacantes y tareas programadas de Celery.
- El adaptador existente de OmniRoute y la deduplicación de vacantes.
- Sin nuevas cuentas o autenticación en las bolsas de empleo, y sin postulación automática.
