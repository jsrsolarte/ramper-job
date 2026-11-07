# Design

## Context

Las vacantes guardan `published_at` cuando la fuente la proporciona. El análisis por perfil no tiene un sello específico de finalización y el seguimiento solo guarda `updated_at`, que hoy se modifica al cambiar estado. Recomendaciones no requiere un registro de seguimiento hasta que la persona lo cambia.

## Goals / Non-Goals

**Goals:**
- Mantener marcas de tiempo separadas para publicación, finalización del análisis y entrada al estado actual.
- Presentar la duración relativa en español y conservar una fecha absoluta accesible.
- Mantener el seguimiento por perfil, dado que una vacante compartida puede tener etapas distintas para cada persona.

**Non-Goals:**
- Inferir fechas de publicación ausentes a partir de la primera vez que el sistema vio la vacante.
- Guardar cada transición histórica como una línea de tiempo completa; se necesita la fecha del estado actual.

## Decisions

- Usar `published_at` como única fuente para «Publicada hace…». No sustituirlo por `first_seen_at`, porque el primer hallazgo no equivale a la fecha publicada por la fuente.
- Registrar la finalización del análisis en el registro de análisis asociado al perfil y la revisión. Así la etiqueta corresponde a la evaluación vigente, no a la última actualización global de la vacante.
- Registrar explícitamente cuándo el seguimiento entra en su estado actual. Cambiar de estado, descartar o restaurar inicia una nueva antigüedad; el dato pertenece al seguimiento del perfil, no a la vacante compartida.
- Mostrar tiempo relativo en el servidor usando la zona horaria configurada y conservar la fecha/hora completa como valor accesible. Un recargo actualiza el texto; no se requiere un contador en tiempo real.
- Para registros antiguos con una fecha confiable existente, reutilizarla como inicio aproximado del estado actual. Omitir cualquier etiqueta cuya fecha no pueda determinarse; no fabricar fechas históricas.
- Alternativa considerada: calcular el estado actual desde `updated_at` y el análisis desde `created_at`. Se descarta como fuente permanente porque `updated_at` puede cambiar por otras ediciones y `created_at` marca la creación/encolado, no la finalización del análisis.

## Risks / Trade-offs

- Los registros históricos pueden no permitir conocer la fecha exacta de una transición → migrar solo fechas sustentadas por datos existentes y omitir las demás.
- Una hora relativa pierde precisión visual → incluir la fecha y hora absoluta en una etiqueta accesible asociada.

## Migration Plan

- Añadir marcas de tiempo compatibles con registros existentes y establecerlas al completar análisis o cambiar de estado.
- Mantener `published_at` nullable; no rellenar vacíos con fechas estimadas.
- Reversión: ocultar las etiquetas y eliminar los campos nuevos solo después de comprobar que no se necesitan para retención o auditoría.
