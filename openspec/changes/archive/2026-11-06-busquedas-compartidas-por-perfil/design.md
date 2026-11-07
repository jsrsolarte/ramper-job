# Design

## Context

El ciclo periódico actual agenda una actualización por perfil. Cada actualización genera términos para ese perfil, consulta las fuentes y guarda publicaciones normalizadas globalmente. El sistema ya crea análisis por combinación de perfil y vacante, valida elegibilidad geográfica y deduplica publicaciones. Las etapas de IA y el seguimiento personal se especifican por separado.

## Goals / Non-Goals

**Goals:**
- Compartir solo el trabajo de consulta externa cuando los criterios que afectan sus resultados sean equivalentes.
- Mantener una relación vacante-perfil para repartir los resultados y crear análisis independientes.
- Respetar versiones de búsqueda y perfiles vigentes para no mezclar generaciones distintas de criterios.

**Non-Goals:**
- Compartir puntajes, evidencia, contenido privado o estados personales entre perfiles.
- Agrupar búsquedas parecidas cuando sus parámetros efectivos no sean iguales.
- Cambiar la rúbrica, los límites de puntaje o la definición de estados de seguimiento.

## Decisions

### Agrupar solicitudes por criterios efectivos, no por similitud del perfil

La identidad de una búsqueda compartible se basa en fuente, términos de búsqueda normalizados, ubicaciones efectivas, modalidad remota y versiones de configuración que afecten la consulta. Ordenar o normalizar espacios no debe crear diferencias artificiales. El CV, la rúbrica y los umbrales no forman parte de esa identidad si no cambian los parámetros enviados a la fuente.

Esto permite reutilizar una consulta idéntica entre perfiles sin inferir que dos perfiles parecidos deben recibir las mismas vacantes. Se descarta agrupar por ciudad solamente, porque distintos términos o modalidad pueden producir resultados distintos.

### Fan-out de publicaciones hacia análisis individuales

La vacante normalizada permanece como registro global único. Para cada perfil que participó en la solicitud compartida se registra o reutiliza la relación de análisis perfil-vacante, después de validar la elegibilidad actual del perfil. Cada relación usa su revisión y configuración vigentes y continúa por las etapas de análisis definidas para ese perfil.

La consulta externa no se repite por cada perfil del grupo. Se descarta compartir una sola evaluación entre perfiles porque CV, rúbrica, umbral y seguimiento son personales.

### Mantener vigencia e idempotencia ante ejecuciones concurrentes

Una actualización obsoleta no debe asociar resultados a una revisión de perfil que ya cambió. El trabajo compartido debe tolerar que coincida con una ejecución manual o periódica y conservar las garantías actuales de deduplicación e idempotencia por perfil-vacante.

## Risks / Trade-offs

- [Una clave de agrupación incompleta puede mezclar consultas distintas] → Incluir todos los parámetros efectivos enviados a cada fuente y sus versiones pertinentes.
- [Cambios de perfil durante la consulta pueden vincular resultados a criterios obsoletos] → Revalidar revisión y preferencias antes de crear las relaciones de análisis.
- [El fan-out puede crear una ráfaga de trabajos] → Encolar análisis individuales con los controles de recuperación, límites y deduplicación existentes.

## Migration Plan

1. Implementar esta optimización después de completar sus prerrequisitos funcionales y antes de stage.
2. Mantener el esquema y las vacantes ya guardadas; ejecuciones posteriores usarán agrupación de consultas y relaciones existentes.
3. Si hay fallos, volver a programar consultas individuales conserva el comportamiento vigente y no requiere migrar datos.
