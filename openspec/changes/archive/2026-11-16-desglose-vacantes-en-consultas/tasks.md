# Tasks

## 1. Instrumentar resultados de ingesta

- [x] 1.1 Extender el servicio de guardado para devolver, junto con las vacantes persistidas, los conteos de nuevas, conocidas, conocidas con cambios materiales y conocidas sin cambios; verificar invariantes con pruebas unitarias de vacantes nuevas, repetidas y actualizadas.
- [x] 1.2 Añadir contadores anulables a `OperationalRun` y crear la migración; verificar que las filas existentes conservan sus datos y quedan con desglose no disponible.
- [x] 1.3 Registrar los conteos al finalizar consultas por perfil y compartidas, manteniendo una sola medición por consulta compartida; verificar con pruebas que el total coincide con nuevas más conocidas y que los fallos previos a clasificar no quedan como ceros.

## 2. Presentar el desglose en observabilidad

- [x] 2.1 Agregar por fuente las sumas de resultados nuevos y conocidos, además de las métricas de cambios, excluyendo valores históricos nulos; verificar agregados en distintos periodos y que las sumas describen ocurrencias de consultas, no vacantes distintas entre consultas.
- [x] 2.2 Mostrar el desglose en cada fila del historial de consultas, con una presentación compacta de conocidas actualizadas y sin cambios; verificar valores nuevos, ceros reales e historial con desglose no disponible.
- [x] 2.3 Confirmar en pruebas del panel que el acceso sigue restringido a administración y que solo se muestran métricas agregadas, sin identidad ni datos privados de perfiles.

## Workflow follow-up

- Sincronizar la especificación principal y archivar este cambio cuando la implementación esté aprobada.
