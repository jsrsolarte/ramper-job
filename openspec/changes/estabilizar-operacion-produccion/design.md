# Design

## Context

Ver `proposal.md` para la motivación. El endpoint `/readyz` verifica PostgreSQL y Redis; `SECURE_SSL_REDIRECT` está activo en producción y las sondas consultan HTTP con el host productivo. La reconciliación de ingestas combina ejecuciones, unidades durables, heartbeats y leases. El prompt de rúbrica se versiona con la configuración; el validador limita el texto de requisito crítico a 180 caracteres y su evidencia a 240. La base y los CV usan volúmenes del nodo, y la documentación no describe copias externas.

## Goals / Non-Goals

**Goals:**

- Dejar las rutas de salud compatibles con el tráfico interno HTTP sin debilitar HTTPS para la navegación de la aplicación.
- Hacer que cada ingesta activa tenga trabajo durable con señal de progreso vigente o que se recupere/cierre en forma acotada.
- Mantener alineados el formato que solicita el prompt y los límites del validador sin guardar contenido rechazado.
- Definir copias externas coherentes para PostgreSQL y CV, con una prueba aislada de restauración.

**Non-Goals:**

- Cambiar, suspender o reanudar Flux en producción como parte del diseño o su implementación por defecto.
- Cambiar la puntuación de compatibilidad o aceptar requisitos críticos que excedan el esquema existente.
- Respaldar Redis, que contiene colas reconstruibles, ni importar datos de staging.

## Decisions

1. **Excluir solo las rutas de salud de la redirección HTTP a HTTPS.** Configurar una excepción limitada a `/healthz` y `/readyz` para que las sondas reciban directamente 200 o una respuesta genérica de no disponibilidad. La navegación ordinaria conserva HTTPS forzado. Se prefiere esta opción a configurar sondas HTTPS sobre Gunicorn HTTP o relajar la política de redirección para toda la aplicación.

2. **Usar heartbeat y vigencia del lease como prueba de progreso de una unidad durable.** La reconciliación debe distinguir una tarea realmente activa de una fila protegida que ya no progresa: reencolar dentro del presupuesto de intentos; al agotarlo, cerrar la unidad, la ejecución y los leases asociados. Aumentar el timeout no resuelve una ejecución que quedó huérfana.

3. **Expresar en el prompt los mismos límites y estados que aplica el validador.** Las instrucciones deben pedir texto de requisito de hasta 180 caracteres y evidencia de hasta 240, y enumerar los estados aceptados. La configuración versionada conserva la trazabilidad; el análisis continúa rechazándose sin persistir respuesta parcial si el modelo incumple el contrato. El cambio no amplía límites ni agrega reintentos de IA que aumentarían coste y latencia.

4. **Respaldar en generaciones emparejadas y fuera del nodo.** Cada generación debe poder asociar la copia lógica de PostgreSQL con los CV correspondientes, registrar metadatos de antigüedad/integridad y conservarse en destino independiente del nodo. Redis queda fuera. Antes de aprovisionar, revisar las opciones aprobadas del repositorio de infraestructura y escoger el destino, frecuencia, retención y objetivos de recuperación; no introducir credenciales ni secretos en Git. La restauración se prueba en un entorno aislado.

## Risks / Trade-offs

- [Una excepción de redirección demasiado amplia podría permitir HTTP en rutas de la aplicación] → limitarla a los dos endpoints genéricos de salud y probar que una ruta normal continúa redirigiendo.
- [El reencolado repetido puede duplicar trabajo] → preservar la idempotencia de las unidades y comprobar su lease antes del despacho.
- [El modelo puede seguir incumpliendo límites] → rechazar con categoría segura, medir la frecuencia agregada y no guardar respuestas completas.
- [Las copias de base y archivos pueden no corresponderse] → crear generaciones identificables y verificar sus asociaciones durante una restauración aislada.
- [El almacenamiento externo puede requerir costo o configuración fuera de este repositorio] → elegirlo y acordar frecuencia/retención antes de habilitar copias; mantener prod sin mutaciones hasta una autorización explícita.

## Migration Plan

1. Implementar y verificar en staging los cambios de salud, prompt y reconciliación con datos sintéticos.
2. Preparar el destino externo, la política de retención y la restauración aislada antes de escribir la primera copia de producción.
3. Revisar el candidato probado y el digest de imagen; cualquier promoción, cambio de workloads o configuración en prod requiere autorización explícita y se aplica por Git/Flux.
4. Observar sondas y ejecuciones agregadas tras el despliegue. Si un cambio de aplicación falla, volver por Git al SHA/digest compatible anterior; restaurar datos solo desde una generación verificada siguiendo el procedimiento aprobado.

## Open Questions

- ¿Qué destino externo ya aprobado ofrece el servidor y qué frecuencia, retención, RPO y RTO se deben configurar? Resolverlo al inspeccionar las opciones existentes antes de implementar la provisión de backups.
