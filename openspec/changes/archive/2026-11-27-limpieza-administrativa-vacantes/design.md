# Design

## Context

El control global actual detiene el inicio de nuevas unidades, pero permite finalizar la unidad activa y conserva tareas en cola. La limpieza debe impedir que mensajes anteriores actúen después del borrado. La base y Redis no comparten una transacción; existe una programación periódica que puede generar trabajo futuro.

## Goals / Non-Goals

**Goals:** limpieza explícita, observable e idempotente con datos protegidos y recuperación segura.

**Non-Goals:** crear backups, alterar horarios, borrar archivos de CV o permitir comandos arbitrarios.

## Decisions

1. Mostrar vista previa por categoría y advertencia de pérdida irreversible; confirmar con texto explícito y POST protegido por CSRF y permisos administrativos. La vista previa no modifica datos. Invalidar la confirmación si cambian el alcance o las precondiciones; no reutilizarla.
2. Registrar una operación durable separada del historial que se va a eliminar. Usar exclusión mutua y un identificador de operación para impedir ejecuciones simultáneas y tolerar reintentos sin repetir acciones destructivas. Mantener auditoría segura incluso en fallos.
3. Guardar el estado y revisión de pausa; activar bloqueo de nuevos productores, esperar que unidades activas terminen e impedir nuevos inicios mediante un control durable de generación. Etiquetar y rechazar tareas antiguas también en recuperación y callbacks; no purgar indiscriminadamente Redis, que comparte resultados y control. Al finalizar, restaurar solo la pausa administrada por la operación si no hubo cambios posteriores.
4. Borrar en una transacción las entidades del alcance y cascadas conocidas; verificar que ninguna cascada alcance cuentas, perfiles, revisiones, archivos, configuración, parámetros, horarios ni la auditoría. Evitar que claves primarias reutilizadas permitan que mensajes anteriores actúen sobre datos nuevos. No almacenar valores privados en vista previa ni auditoría.
5. Si el proceso falla o se interrumpe, registrar estado durable, no afirmar éxito y mantener pausa cuando no se pueda demostrar seguridad. Definir recuperación idempotente y manejo de un fallo posterior al commit para no repetir el borrado. Actualizar la fecha de cobertura operativa en la misma transacción del borrado.

## Risks / Trade-offs

- [Pérdida permanente] → advertir alcance y ausencia de respaldo; confirmación explícita para cada ejecución.
- [Carrera entre cola, transacción y productores] → generación durable, barrera de entrada y pruebas de concurrencia, mensajes demorados y caídas en cada fase.
- [Tiempo de espera prolongado] → estado visible y límite seguro; abortar antes de borrar si no se alcanza inactividad.
- [Una búsqueda posterior recrea vacantes] → informar al usuario y respetar horarios y estado previo.

## Migration Plan

Implementar y validar con datos sintéticos aislados y staging, incluyendo interrupciones y auditoría; no ejecutar la limpieza en producción como parte del despliegue. Aplicar migraciones compatibles y definir reversión de código sin restaurar datos borrados. La promoción y cada limpieza productiva requieren autorización específica.

## Validación de implementación

- La vista previa y la operación se probaron con PostgreSQL efímero y filas sintéticas. Los casos confirman conservación de cuentas, perfil, ruta de CV, revisión, configuración, parámetro, horario y auditoría.
- La barrera de generación marca mensajes al publicarse; durante la limpieza bloquea ejecuciones y después descarta generaciones anteriores. La eliminación solo ocurre cuando no hay unidades activas; timeout, rollback e interrupción dejan el procesamiento pausado.
- La suite dirigida completa aprobó 98 pruebas; el sistema Django y las migraciones no presentan errores. OpenSpec valida los artefactos de los tres cambios.
- La operación no crea backups ni elimina archivos. El flujo todavía requiere validación integrada en staging antes de cerrar esta tarea; no se ejecutó una limpieza contra ningún entorno compartido.
