# Design

## Context

`operations.scheduling.next_periodic_refresh_schedule` calcula `last_started_at + intervalo` y expone `is_overdue`; fuera de la franja puede devolver una fecha pasada. Las plantillas del dashboard y centro administrativo muestran `next_at` sin comprobar esa señal. Beat usa un intervalo independiente y el inicio global se registra al reclamar el ciclo; una fecha vencida no demuestra por sí misma si Beat, worker, cola o estado fallaron.

## Goals / Non-Goals

**Goals:**
- Mantener un estado compartido coherente, claro en ambas pantallas y sin nuevas ejecuciones por lectura.
- Identificar si hay un defecto de programación reproducible con pruebas controladas, sin suponer causas de producción.

**Non-Goals:**
- Reiniciar procesos, lanzar búsquedas o modificar producción desde la consulta o esta planificación.
- Proyectar fechas futuras sumando intervalos sin comprobar ejecuciones reales.

## Decisions

- Tratar como vencida una estimación `next_at <= ahora` cuando no se aplica pausa global ni franja horaria activa. Conservar la hora original como vencida, no desplazarla artificialmente. Mostrar último inicio en administración si existe. Estado global y franja tienen precedencia; una estimación sin datos fiables queda como no disponible.
- Compartir presentación y semántica de estados entre ambas vistas. Si la página permanece abierta al alcanzar la hora, refrescar únicamente el estado por una solicitud de lectura autenticada o indicar que debe actualizarse; no cambiar la página completa ni ejecutar trabajo. Al fallar la consulta, indicar que el estado no está actualizado en lugar de afirmar que el ciclo comenzó.
- Consultar los lotes y unidades durables de `RefreshBatch` y `RefreshWorkItem`, su origen, estado y vigencia de actividad o concesión. Distinguir una unidad efectivamente activa de trabajo en cola, diferido o con concesión vencida; no deducir actividad solo del último inicio del ciclo. La actividad y la próxima estimación se muestran como dimensiones independientes, incluso con una pausa activa. Evitar exponer perfiles o consultas privadas en el dashboard.
- Revisar y probar con reloj controlado la relación entre Beat, `claim_periodic_refresh_start`, franja y recuperación tras interrupciones. Si se reproduce un defecto que impide iniciar el ciclo debido, corregirlo en el flujo de implementación y probar ausencia de ciclos duplicados. Si no se reproduce, conservar el aviso de retraso y documentar la evidencia sin adjudicar causa.
- La revisión de producción del 26 de noviembre observó envío por Beat a las 16:34:35, reinicio de Beat a las 17:29 y repetidos reinicios del worker por fallos de liveness; los logs disponibles no prueban si el ciclo se procesó. Investigar en pruebas la desincronización entre la agenda persistente de Beat y la marca del ciclo, y las sondas que agotan su plazo, sin suponer que estos hechos explican por completo el incidente.
- La inspección del código confirma que `DatabaseRefreshInterval.is_due` vuelve a leer el intervalo persistido; `refresh_periodic_sources` respeta ambas pausas y `claim_periodic_refresh_start` bloquea la fila dentro de una transacción, por lo que una segunda entrega dentro del intervalo se descarta. La marca representa el inicio reclamado, no el éxito del ciclo. Las pruebas cubren intervalo dinámico, reclamación repetida y un ciclo que inicia después de mostrarse retrasado.
- La configuración base del worker ejecuta `celery ping` con timeout interno de 3 s y liveness de Kubernetes de 5 s. El overlay de staging usa comprobaciones TCP para startup/readiness y liveness Celery con timeout de 30 s; el overlay productivo conserva la configuración base. En una red Docker interna, un worker de una concurrencia respondió el ping de 3 s mientras ejecutaba una tarea artificial de 35 s. No se reprodujo el reinicio. Esta simulación no demuestra que la causa de producción haya sido descartada; no se modifica la configuración productiva.
- Como las tres propuestas locales se implementan en el mismo candidato, `VERSION` debe reflejar el conjunto: las alertas y la limpieza administrativa agregan capacidades compatibles, así que el incremento final será MINOR aunque este cambio aislado describa una corrección PATCH.
- Distinguir el inicio registrado del éxito o finalización de búsquedas; el indicador no pretende certificar resultados. Si no hay estado inicial fiable, no convertir el tiempo transcurrido desde cada petición en una fecha siempre futura.

## Risks / Trade-offs

- [Una fecha vencida refleja retraso breve normal de cola] → Usar lenguaje de pendiente o retraso, sin afirmar avería.
- [La pantalla abierta queda desactualizada o pierde conexión] → Indicar falta de actualización y no desplazar la fecha sin evidencia.
- [Cambios al planificador duplican trabajo] → Reutilizar la reserva atómica y probar reanudación, concurrencia y pausas con fuentes simuladas.

## Migration Plan

Priorizar cambios de lectura y presentación; no se prevé migración de datos. Probar con reloj y fuentes simulados, y validar en staging autorizado. Producción requiere autorización explícita; no ejecutar tareas reales para diagnosticar sin acuerdo operativo.
