# Proposal

## Why

La revisión del 12 de noviembre de 2026 confirmó que prod ya está activo, pero la guía del proyecto aún dice que no hay despliegue productivo. También mostró avisos repetidos en las sondas de salud, rechazos de análisis por longitud inválida en requisitos críticos, ejecuciones de ingesta antiguas aún abiertas y ausencia documentada de backups. Hace falta alinear las reglas del sistema con esos comportamientos y reducir el riesgo operativo antes de depender de datos reales.

## What Changes

- Definir sondas de producción que respondan correctamente sin seguir redirecciones HTTPS y sin revelar información interna.
- Precisar la recuperación de unidades de ingesta protegidas que no tienen heartbeat o lease vigente, para que no queden ejecuciones activas indefinidamente.
- Alinear las instrucciones del modelo y la validación de texto de requisitos críticos, manteniendo categorías seguras y sin persistir respuestas inválidas.
- Definir backups externos para la base de datos y los CV de producción, con restauración documentada y comprobada.
- Corregir `AGENTS.md` para describir el estado vivo de prod y conservar las salvaguardas de autorización para cambios futuros.

## Capabilities

### New Capabilities

- `despliegue-produccion`: sondas de salud productivas compatibles con HTTPS forzado.
- `respaldo-datos-produccion`: copias externas y restauración de los datos persistentes de producción.

### Modified Capabilities

- `observabilidad-operativa`: cerrar o reencolar trabajo de ingesta sin progreso vigente y evitar ejecuciones indefinidas.
- `compatibilidad-vacantes`: alinear las instrucciones de salida de requisitos críticos con los límites que aplica el validador.

## Impact

- Aplicación: middleware de HTTPS, endpoints `/healthz` y `/readyz`, prompts y validación de análisis, reconciliación de trabajo de ingesta.
- Entorno: producción en Kubernetes y Flux; no se cambia ni reconcilia el clúster al preparar esta propuesta.
- Datos: PostgreSQL y archivos CV persistidos en volúmenes del nodo; la ubicación externa, retención y prueba de restauración se elegirán en el diseño antes de implementar backups.
- Documentación: `AGENTS.md` reflejará el estado productivo observado y mantendrá explícita la autorización requerida para mutaciones futuras.
