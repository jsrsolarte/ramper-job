# Proposal

## Why

La administración solo ve el estado más reciente de cada fuente y no dispone de un historial para entender tendencias, retrasos o fallas repetidas. Un panel operativo con volúmenes y tiempos permitirá detectar si la ingesta y el análisis están funcionando como se espera.

## What Changes

- Añadir un panel restringido a administración para consultar métricas agregadas por periodo.
- Registrar historial mínimo de ejecuciones de ingesta y análisis para calcular duraciones, resultados y errores.
- Mostrar volumen de cola y antigüedad de análisis pendientes junto con el último resultado por fuente.
- Mostrar la cobertura temporal disponible y evitar exponer CV, prompts o datos privados de perfiles.

## Capabilities

### New Capabilities

- `observabilidad-operativa`: métricas y salud histórica de los procesos principales para administración.

### Modified Capabilities

## Impact

- Tareas de ingesta y análisis para guardar eventos de ejecución y tiempos.
- Almacenamiento histórico acotado y consultas agregadas.
- Panel interno de administración, accesible solo a personal autorizado.
