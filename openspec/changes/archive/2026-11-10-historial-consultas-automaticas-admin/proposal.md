# Proposal

## Why

El panel de administración resume cuántas consultas a fuentes hubo, pero solo presenta una lista cronológica para comandos manuales. Por eso no permite comprobar de un vistazo cuándo corrieron las búsquedas automáticas ni qué resultado tuvo cada consulta.

## What Changes

- Añadir al panel de observabilidad un historial cronológico de consultas de fuentes, incluidas las automáticas.
- Mostrar fecha, fuente, estado, vacantes encontradas, duración y resumen seguro del error, cuando exista.
- Aplicar el periodo seleccionado y permitir revisar páginas anteriores del historial.

## Capabilities

### New Capabilities

### Modified Capabilities
- `observabilidad-operativa`: permitir consultar ejecuciones individuales de búsqueda además de sus métricas agregadas.

## Impact

Afecta el tablero administrativo de observabilidad, su consulta de ejecuciones operativas y sus pruebas. No modifica el planificador, la frecuencia de búsqueda ni la extracción de datos.
