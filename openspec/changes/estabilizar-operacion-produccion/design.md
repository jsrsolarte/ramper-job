# Design

## Context

Ver `proposal.md` para la motivación. El endpoint `/readyz` verifica PostgreSQL y Redis; `SECURE_SSL_REDIRECT` está activo en producción y las sondas consultan HTTP con el host productivo. La reconciliación de ingestas combina ejecuciones, unidades durables, heartbeats y leases. El prompt de rúbrica se versiona con la configuración; el validador limita el texto de requisito crítico a 180 caracteres y su evidencia a 240. La base y los CV usan volúmenes del nodo. La documentación ya registra que no hay backups y que su pérdida sería irreversible; backups y restauración no forman parte de este cambio.

## Goals / Non-Goals

**Goals:**

- Dejar las rutas de salud compatibles con el tráfico interno HTTP sin debilitar HTTPS para la navegación de la aplicación.
- Hacer que cada ingesta activa tenga trabajo durable con señal de progreso vigente o que se recupere/cierre en forma acotada.
- Mantener alineados el formato que solicita el prompt y los límites del validador sin guardar contenido rechazado.

**Non-Goals:**

- Cambiar, suspender o reanudar Flux en producción como parte del diseño o su implementación por defecto.
- Cambiar la puntuación de compatibilidad o aceptar requisitos críticos que excedan el esquema existente.
- Respaldar Redis, que contiene colas reconstruibles, ni importar datos de staging.
- Configurar backups o ejecutar restauraciones de PostgreSQL y CV; quedan pospuestos para un cambio futuro.

## Decisions

1. **Excluir solo las rutas de salud de la redirección HTTP a HTTPS.** Configurar una excepción limitada a `/healthz` y `/readyz` para que las sondas reciban directamente 200 o una respuesta genérica de no disponibilidad. La navegación ordinaria conserva HTTPS forzado. Se prefiere esta opción a configurar sondas HTTPS sobre Gunicorn HTTP o relajar la política de redirección para toda la aplicación.

2. **Usar heartbeat y vigencia del lease como prueba de progreso de una unidad durable.** La reconciliación debe distinguir una tarea realmente activa de una fila protegida que ya no progresa: reencolar dentro del presupuesto de intentos; al agotarlo, cerrar la unidad, la ejecución y los leases asociados. Aumentar el timeout no resuelve una ejecución que quedó huérfana.

3. **Expresar en el prompt los mismos límites y estados que aplica el validador.** Las instrucciones deben pedir texto de requisito de hasta 180 caracteres y evidencia de hasta 240, y enumerar los estados aceptados. La configuración versionada conserva la trazabilidad; el análisis continúa rechazándose sin persistir respuesta parcial si el modelo incumple el contrato. El cambio no amplía límites ni agrega reintentos de IA que aumentarían coste y latencia.

## Risks / Trade-offs

- [Una excepción de redirección demasiado amplia podría permitir HTTP en rutas de la aplicación] → limitarla a los dos endpoints genéricos de salud y probar que una ruta normal continúa redirigiendo.
- [El reencolado repetido puede duplicar trabajo] → preservar la idempotencia de las unidades y comprobar su lease antes del despacho.
- [El modelo puede seguir incumpliendo límites] → rechazar con categoría segura, medir la frecuencia agregada y no guardar respuestas completas.
- [La pérdida del nodo puede eliminar PostgreSQL y los CV al no existir backups] → conservar documentado el riesgo de pérdida irreversible; posponer backups y restauración para una decisión futura separada.

## Migration Plan

1. Implementar y verificar en staging los cambios de salud, prompt y reconciliación con datos sintéticos.
2. Revisar el candidato probado y el digest de imagen; cualquier promoción, cambio de workloads o configuración en prod requiere autorización explícita y se aplica por Git/Flux.
3. Observar sondas y ejecuciones agregadas tras el despliegue. Si un cambio de aplicación falla, volver por Git al SHA/digest compatible anterior.

## Open Questions

Backups y restauración quedan pospuestos. Si se priorizan más adelante, definirlos en un cambio independiente.
