# Proposal

## Why

El dashboard no permite registrar qué vacantes se descartaron ni en cuáles ya se inició una postulación. Un flujo de seguimiento por perfil permitirá avanzar las oportunidades por etapas ordenadas, cerrar procesos que no continuaron y conservar las vacantes descartadas por separado.

## What Changes

- Registrar por perfil un estado personal independiente del ciclo de análisis de IA: pendiente de decisión, aplicada, en proceso, entrevista, finalizada o descartada.
- Restringir el avance al flujo Recomendaciones → Aplicadas → En proceso → Entrevista; permitir finalizar desde una etapa de postulación y descartar desde cualquier estado.
- Al restaurar una vacante descartada, devolverla al estado que tenía antes de descartarla.
- Mostrar recomendaciones y estados de seguimiento como pestañas del dashboard con conteos de vacantes visibles.
- Ordenar las pestañas así: por analizar, recomendaciones, aplicadas, en proceso, entrevista, finalizadas y descartadas.

## Capabilities

### New Capabilities

- `seguimiento-postulaciones`: registrar y consultar el avance personal de cada vacante para un perfil.

### Modified Capabilities

- `dashboard-vacantes`: filtrar las recomendaciones por estado de seguimiento y mostrar pendientes por defecto.

## Impact

- Persistencia del seguimiento por perfil y vacante, incluido el estado previo a un descarte.
- Validación de transiciones y acciones, filtros, conteos y etiquetas en el dashboard.
- No requiere cambios al scraping ni al proveedor de IA.
