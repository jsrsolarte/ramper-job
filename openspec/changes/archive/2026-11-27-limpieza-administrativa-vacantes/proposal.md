# Proposal

## Why

La limpieza de vacantes y su historial requiere actualmente intervención técnica directa y una pausa coordinada. Administración necesita un procedimiento explícito y verificable que preserve cuentas, perfiles y configuración.

## What Changes

- Ofrecer a administración una vista previa de las cantidades y el alcance de una limpieza irreversible de vacantes, análisis, seguimientos y operaciones de búsqueda.
- Exigir confirmación explícita para cada ejecución y coordinar pausa, drenaje, invalidación de trabajo anterior y borrado transaccional.
- Conservar usuarios, perfiles, revisiones, CV, configuraciones, horarios, parámetros y auditoría de la limpieza; informar el resultado y restaurar el estado de pausa previo de forma segura.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `comandos-administrativos`: operación administrativa restringida para limpiar datos de vacantes con confirmación y auditoría.
- `control-operativo-aplicacion`: coordinación de la pausa y protección frente a trabajo anterior.
- `observabilidad-operativa`: informar el reinicio de cobertura del historial y resultado de la limpieza.

## Impact

Afecta centro administrativo, tareas Celery, persistencia de vacantes y datos asociados, auditoría, métricas y pruebas. No incluye copia de seguridad, restauración, borrado de perfiles ni despliegue a producción. La ausencia de backup debe comunicarse antes de confirmar.
