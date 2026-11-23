# Proposal

## Why

Las búsquedas automáticas consultan fuentes también durante la noche. Hace falta restringir su horario y permitir que administración ajuste la pausa según la operación.

## What Changes

- Configurar una franja diaria de pausa para búsquedas automáticas, habilitada inicialmente de 21:00 a 07:00 en `America/Bogota`.
- Evitar nuevas consultas automáticas durante la franja, conservar trabajos pendientes y reanudar al terminarla sin acumular ciclos vencidos.
- Mostrar la pausa y una estimación coherente de la próxima búsqueda; conservar la pausa global y la pausa individual.
- Mantener disponibles búsquedas manuales administrativas y análisis de vacantes existentes, sujetos a la pausa global existente.

## Capabilities

### New Capabilities

### Modified Capabilities

- `programacion-busquedas`: franja diaria configurable, ejecución y comunicación de la pausa nocturna.

## Impact

- Parámetros y vistas administrativas, planificación Celery, ejecución y recuperación de búsquedas, dashboard y pruebas.
- Requiere distinguir el origen automático del manual en trabajo durable compartido. No cambia datos de vacantes ni despliega por sí mismo.
