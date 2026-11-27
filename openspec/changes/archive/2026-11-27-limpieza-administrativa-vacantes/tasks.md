# Tasks

## 1. Autorización y vista previa

- [x] 1.1 Crear vista previa administrativa con alcance, conteos, advertencia de irreversibilidad y estado de backup; verificar permisos, CSRF y ausencia de datos personales con pruebas sintéticas.
- [x] 1.2 Exigir confirmación específica de una sola ejecución y exclusión mutua; verificar que solicitudes duplicadas, vencidas o sin permiso no inician limpieza.

## 2. Coordinación y borrado

- [x] 2.1 Implementar operación durable, pausa y barrera de generación para productores, workers y callbacks; probar concurrencia, trabajo activo, tareas demoradas y expiración segura.
- [x] 2.2 Implementar borrado transaccional limitado y protección de usuarios, perfiles, CV, configuraciones, parámetros, horarios y auditoría; verificar cascadas y rollback con datos sintéticos.
- [x] 2.3 Implementar recuperación idempotente, restauración del estado previo de pausa y tratamiento de fallos antes y después del commit; probar interrupciones y cambios concurrentes de pausa.

## 3. Auditoría y validación

- [x] 3.1 Registrar actor, fecha, resultado y conteos seguros, y actualizar cobertura operativa; verificar que la auditoría persiste y no contiene datos privados.
- [x] 3.2 Verificar en staging con datos sintéticos todo el flujo, incluyendo tareas antiguas, fallo de worker y ausencia de backup; documentar resultados y evitar ejecución en producción sin autorización específica.

> Validación manual en staging confirmada por el usuario el 2026-11-27.
