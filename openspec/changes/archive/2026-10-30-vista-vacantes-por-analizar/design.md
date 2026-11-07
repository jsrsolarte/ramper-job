# Design

## Context

`Vacancy` guarda el contenido fuente compartido y `VacancyAnalysis` relaciona la vacante con un perfil y una revisión. Su estado `pending` representa el análisis aún no completado o en reintento.

## Goals / Non-Goals

**Goals:**

- Consultar análisis pendientes del perfil y revisión vigentes.
- Reutilizar los datos almacenados de la publicación original.

**Non-Goals:**

- Cambiar la programación de tareas de IA o crear un segundo mecanismo de cola.
- Exponer vacantes o análisis de otros perfiles.

## Decisions

- La bandeja consultará análisis `pending` del perfil actual y su revisión vigente. Se reutiliza esta cola por perfil para mantener la elegibilidad y el aislamiento que ya aplica el dashboard.
- La plantilla leerá los campos originales de `Vacancy`; no reutilizará las propiedades derivadas que el dashboard prepara para análisis completados. Así no se presentan como hechos resultados de IA inexistentes.
- La vista será una pestaña del mismo dashboard de vacantes. Las pestañas separan la cola técnica pendiente de las recomendaciones listas para decidir, y muestran el conteo de vacantes únicas visibles para el perfil actual.

## Risks / Trade-offs

- **La cola puede incluir reintentos por error de IA** → Mostrar el mensaje de error disponible, si existe, sin cambiar el estado del análisis.
- **Una vacante puede tener varios análisis pendientes si se reprocesa** → Presentar una sola publicación por perfil, seleccionando el análisis vigente.

## Migration Plan

No requiere migración de datos. Desplegar la pestaña y su consulta junto con el dashboard existente; la reversión elimina únicamente la pestaña y su navegación.
