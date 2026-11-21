# Design

## Context

`refresh_periodic_sources` registra el inicio y delega a `refresh_sources`; las actualizaciones individuales, manuales y los lotes reanudables comparten tuberías. `RefreshWorkItem` divide consultas y detalles y permite recuperación. La pausa global detiene búsquedas y análisis, mientras la pausa individual restringe perfiles. La estimación actual usa el último inicio y el intervalo. Ver delta para el contrato.

## Goals / Non-Goals

**Goals:**
- Restringir llamadas automáticas a fuentes, incluso tras recuperación y cambios de perfil, manteniendo ejecución manual.
- Hacer visible la franja y la estimación sin modificar las pausas existentes.

**Non-Goals:**
- Interrumpir una petición en vuelo o detener análisis de vacantes existentes.
- Cambiar infraestructura o ejecutar tareas externas durante la planificación.

## Decisions

- Guardar configuración global habilitada y horas de inicio y fin con valores iniciales 21:00 y 07:00 en `America/Bogota`. Comparar horas locales con inicio inclusivo y fin exclusivo, soportando cruce de medianoche y franjas de un mismo día; rechazar horas iguales. Aplicar cambios inmediatamente y registrar auditoría administrativa según los patrones existentes.
- Propagar origen automático o manual en el lote y trabajo durable; no inferirlo de `command_run_id` sin comprobar todos los caminos. Definir migración conservadora para trabajo anterior de origen desconocido: tratarlo como automático hasta terminar la franja. Para trabajo compartido entre orígenes, separar unidades o asegurar que el manual no provoque la ejecución automática durante la franja; mantener aislamiento y deduplicación por perfil.
- Comprobar la franja antes del ciclo global y justo antes de cada unidad de consulta o detalles, incluidos reintentos y recuperación. Una unidad ya iniciada puede finalizar; guardar el cursor y dejar pendiente la siguiente. Reanudar al fin de la franja usando programación limitada y trabajo durable, sin reencolar cada minuto ni generar tormenta de ciclos. Coordinar leases para evitar que caduquen como errores o bloqueen la reanudación.
- Al reabrir, ejecutar como máximo un ciclo global vencido y reanudar unidades pendientes sin duplicados; conservar el intervalo y registrar la hora real de inicio, nunca la de un ciclo omitido. Recalcular la estimación compartida al modificar la franja, intervalo o pausa global. La estimación es aproximada y no garantiza ejecución exacta a las 07:00.
- No reutilizar `processing_paused` para la franja: también bloquearía análisis y trabajo manual. Las búsquedas manuales respetan pausa global y exclusiones individuales existentes. Evaluar el estado actualizado de cada perfil al reanudar.

## Risks / Trade-offs

- [Origen mezclado o desconocido deja escapar llamadas nocturnas] → Persistir origen y probar todos los puntos de entrada, recuperación y migración conservadora.
- [Una unidad ya iniciada termina después del inicio] → Limitar la unidad actual y probar que no arranca la siguiente.
- [Colas, leases o cambios de horario causan duplicados o trabajo perdido] → Usar el mecanismo durable y pruebas de concurrencia, expiración y modificación durante la pausa.
- [No hay datos suficientes para estimar] → Mostrar estado no disponible, no fabricar una fecha.

## Migration Plan

Aplicar migración de parámetros y origen conservador, verificar con datos sintéticos y reloj controlado, y probar en staging autorizado. Al revertir, retirar la restricción programada sin alterar la pausa global; revisar compatibilidad de datos durables antes de revertir migraciones. Producción requiere autorización explícita.
