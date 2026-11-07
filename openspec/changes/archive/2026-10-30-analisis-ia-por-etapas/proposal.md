# Proposal

## Why

Hoy una sola llamada de IA puntúa la compatibilidad de una vacante con un perfil y también organiza la publicación, incluso cuando el puntaje queda bajo el mínimo del perfil. Separar ambos trabajos permite mostrar el puntaje primero y reservar el enriquecimiento más detallado para vacantes relevantes, midiendo tokens y duración para comprobar el ahorro.

## What Changes

- Dividir el análisis en una etapa de puntaje por perfil y otra etapa asíncrona de organización de la publicación.
- Ejecutar la organización cuando el puntaje alcance el mínimo vigente del perfil, reutilizando el resultado por vacante y configuración.
- Permitir reanudar el enriquecimiento de resultados ya puntuados cuando el mínimo del perfil baje.
- Registrar duración y tokens informados por el proveedor por etapa, sin tratar datos de uso ausentes como cero.
- Mantener la validación de ubicación previa a las llamadas de IA.

## Capabilities

### New Capabilities

### Modified Capabilities

- `compatibilidad-vacantes`: el puntaje se calcula y conserva por separado del enriquecimiento, con seguimiento de etapa y telemetría de uso.
- `presentacion-vacantes`: la descripción organizada puede completarse después del puntaje y mostrarse cuando esté disponible.

## Impact

- Tareas, cliente y validadores de `matching`; modelo `VacancyAnalysis` y almacenamiento reutilizable del contenido organizado por vacante/configuración.
- Dashboard para distinguir puntaje disponible de contenido organizado pendiente o fallido.
- Registro de uso por etapa para su agregación posterior en el panel administrativo de observabilidad operativa.
- Las llamadas de puntuación siguen usando CV y vacante; las de organización usan solo la publicación y su configuración.
- Antes de aplicar el cambio en local, limpiar vacantes y datos asociados; conservar cuentas, perfiles y configuración. No ejecutar esa limpieza en producción.
