# Design

## Context

La página de estadísticas agrega estados personales, disponibilidad registrada en la vacante y puntajes. La disponibilidad externa no se sincroniza con Elempleo y no se monitoreará.

## Goals / Non-Goals

**Goals:**
- Quitar los conteos de disponibilidad de la página y de su contexto de estadísticas.
- Mantener intactos los estados personales por perfil-vacante.

**Non-Goals:**
- Eliminar el campo de disponibilidad del modelo de vacante o cambiar el scraping.
- Tratar vacantes descartadas como cerradas.

## Decisions

- Retirar el cálculo y la tarjeta del panel; el modelo puede conservar su estado de disponibilidad para otros usos existentes, pero no se agregará como métrica administrativa.
- Quitar de la especificación vigente el requisito de disponibilidad y preservar el requisito de seguimiento.

## Risks / Trade-offs

- Quien administre ya no tendrá un resumen de disponibilidad en esta pantalla → coherente con que el sistema no mantiene ni valida ese dato.

## Migration Plan

No requiere migración de base de datos. El rollback restaura el cálculo, la tarjeta y el requisito, si en el futuro se decide monitorear disponibilidad con una fuente confiable.
