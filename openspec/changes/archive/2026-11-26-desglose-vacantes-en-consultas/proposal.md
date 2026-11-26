# Proposal

## Why

La observabilidad actual solo registra cuántas vacantes devolvió una consulta. Ese número no permite saber si la búsqueda está ampliando el catálogo o si vuelve a encontrar publicaciones conocidas; en producción vimos 148 resultados, de los cuales 16 eran nuevos y 132 ya estaban registrados. La consola debe exponer este desglose por ejecución para que el volumen de scraping sea interpretable.

## What Changes

- Registrar, por consulta a una fuente, el total de resultados únicos, cuántas vacantes se agregaron por primera vez y cuántas ya existían.
- Distinguir, entre las vacantes conocidas, las que tuvieron cambios materiales y las que no cambiaron.
- Mostrar el desglose en el historial de consultas y agregar sumas por fuente para el periodo seleccionado, aclarando que son ocurrencias entre ejecuciones y no vacantes distintas en todo el periodo.
- Mantener los registros históricos anteriores al cambio como «sin desglose» en lugar de presentarlos como ceros.

## Capabilities

### New Capabilities

<!-- No se crea una capacidad nueva: el cambio amplía las métricas de observabilidad ya existentes. -->

### Modified Capabilities

- `observabilidad-operativa`: ampliar las métricas de ingesta con resultados nuevos, conocidos, actualizados y sin cambios por consulta.

## Impact

- `jobs.services` y los flujos de actualización por perfil y compartidos para calcular los contadores en el momento de guardar resultados.
- Modelo `OperationalRun` y su migración para conservar el desglose asociado a cada consulta.
- Vista y plantilla de observabilidad operativa para mostrar contadores por ejecución y agregados por fuente.
- Pruebas de ingesta y del panel administrativo.
