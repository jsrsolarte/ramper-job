# Design

## Context

`Vacancy` se comparte entre perfiles y `VacancyAnalysis` se versiona por perfil, revisión y configuración. El estado `pending` de un análisis es técnico y no representa una decisión de postulación.

## Goals / Non-Goals

**Goals:**

- Persistir el seguimiento personal de una vacante aunque su análisis se reprocesa.
- Mantener el estado independiente para cada perfil y proteger las acciones con el alcance de la cuenta autenticada.

**Non-Goals:**

- Enviar postulaciones o inferir automáticamente el progreso.
- Añadir etapas distintas a las descritas en la spec.

## Decisions

- Crear un registro de seguimiento único por `(perfil, vacante)` con valores internos estables: `pending`, `applied`, `in_progress`, `interview`, `finalized` y `discarded`. La ausencia de registro equivale a pendiente de decisión; se persiste al primer cambio de la persona.
- Mantener el estado fuera de `VacancyAnalysis`, ya que ese análisis puede reemplazarse al cambiar la revisión o la configuración y no debe borrar el seguimiento.
- Validar en el servidor el flujo permitido: `pending → applied → in_progress → interview`. Desde `applied`, `in_progress` o `interview` se puede pasar a `finalized` cuando el proceso termina sin continuar. No se permiten saltos ni retrocesos entre etapas.
- Permitir pasar a `discarded` desde cualquier estado, incluido `finalized`. Guardar la etapa anterior en `previous_status`; al restaurar, recuperar esa etapa y no asumir siempre `pending`.
- Limitar las acciones al perfil de la persona autenticada y protegerlas con CSRF. La interfaz ofrece solo los siguientes cambios válidos, más descartar cuando corresponda; «Recomendaciones» representa `pending`.
- Calcular los conteos sobre vacantes únicas visibles por estado y perfil; actualizar las pestañas de origen y destino al cambiar un estado. El orden será «Por analizar», «Recomendaciones», «Aplicadas», «En proceso», «Entrevista», «Finalizadas» y «Descartadas».

## Risks / Trade-offs

- **El registro de seguimiento puede acumularse** → La unicidad por perfil y vacante evita duplicados aunque existan varias versiones de análisis.
- **La ausencia de fila representa un estado válido** → Usar el mismo estado predeterminado en lectura y escritura, con pruebas para evitar que se interprete distinto entre vistas.
- **Seguimientos descartados anteriores no tienen etapa previa guardada** → La migración inicializa su etapa de restauración en `pending`; los descartes nuevos conservarán la etapa real.

## Migration Plan

Ampliar la tabla con el estado `finalized` y el campo `previous_status`. Inicializar este último en `pending` para los registros existentes; las recomendaciones sin seguimiento siguen interpretándose como pendientes. Aplicar la migración antes de desplegar las transiciones y filtros. La reversión debe conservar la tabla y los estados capturados; revertir el esquema podría perder el historial de seguimiento.
