# Design

## Context

Las búsquedas de fuentes seleccionan perfiles por cuenta activa y CV, y agrupan perfiles con solicitudes equivalentes. Guardar preferencias o un CV nuevo también puede encolar una actualización de búsqueda. La pausa global existente detiene todo el procesamiento de la plataforma; esta decisión independiente excluye un perfil individual de la búsqueda por fuentes.

## Goals / Non-Goals

**Goals:**
- Añadir un estado persistente e independiente de búsqueda por perfil.
- Aplicarlo en los ciclos periódicos, las actualizaciones de perfil, las búsquedas administrativas y la distribución de resultados de consultas compartidas.
- Evitar que cambiar solo el interruptor genere revisiones o análisis adicionales.

**Non-Goals:**
- Desactivar el acceso de la cuenta o el perfil, borrar datos o cambiar el CV y las preferencias.
- Detener análisis de vacantes ya guardadas o vacantes nuevas registradas manualmente por administración.
- Reemplazar la pausa global de búsqueda y análisis.

## Decisions

- Guardar el estado de búsqueda como una preferencia propia de `Profile`, independiente de `ProfileRevision`. Usar habilitado como valor inicial para perfiles existentes y nuevos, conservando el comportamiento actual.
- Excluir perfiles pausados al formar solicitudes de búsqueda, incluida la búsqueda manual administrativa. Si una consulta es compartida, usar solo los perfiles habilitados para solicitarla y recibir sus resultados.
- Revalidar el estado antes de iniciar una tarea de perfil y antes de asociar resultados o encolar análisis. Si un perfil se pausa mientras una solicitud compartida está en curso, la consulta puede terminar para otros perfiles habilitados, pero no generar asociaciones nuevas para el perfil pausado.
- Omitir las tareas de búsqueda en cola para un perfil pausado, sin reintentarlas. Al reactivar el interruptor, el perfil vuelve a participar en el siguiente ciclo normal; no se recuperan las tareas omitidas ni se inicia una búsqueda inmediata.
- Mantener separado el flujo de análisis de vacantes existentes o registradas manualmente. Cambiar el estado de búsqueda por sí solo no crea una revisión de perfil ni encola análisis.
- Aplicar la pausa global existente como control de mayor alcance: si está activada, tampoco inician búsquedas los perfiles que individualmente estén habilitados.

## Risks / Trade-offs

- [Una tarea puede iniciar al mismo tiempo que cambia el interruptor] → Comprobar el estado tanto al ejecutar la tarea como antes de distribuir sus resultados.
- [Una búsqueda compartida puede seguir ejecutándose aunque uno de sus perfiles se pause] → No cancelar el trabajo necesario para otros perfiles; excluir al perfil pausado al guardar relaciones y encolar análisis.
- [La palabra «búsqueda» puede confundirse con analizar una vacante ya conocida] → La interfaz y la guía deben aclarar que el control pausa la búsqueda automática de fuentes, no el acceso al perfil ni el análisis de vacantes manuales o ya guardadas.

## Migration Plan

- Inicializar perfiles existentes con búsqueda habilitada y usar ese mismo valor para perfiles nuevos.
- No requiere modificar revisiones históricas, análisis, resultados o relaciones de vacantes.
- Si se revierte la funcionalidad, conservar los datos existentes y volver a incluir todos los perfiles activos con CV en las búsquedas como hoy.
