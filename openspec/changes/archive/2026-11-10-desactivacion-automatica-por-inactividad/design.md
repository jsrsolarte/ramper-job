# Design

## Context

La consola ya permite a la única persona administradora activar y desactivar cuentas, y las cuentas desactivadas conservan sus datos. La automatización requiere una señal confiable de uso autenticado, un proceso periódico y una recuperación clara para la persona afectada. La motivación está en proposal.md y los comportamientos en la delta spec.

## Goals / Non-Goals

**Goals:**
- Medir actividad real en la aplicación con un plazo global de siete días.
- Evitar desactivar por inactividad a la cuenta administrativa.
- Preservar acceso administrativo para reactivar una cuenta sin pérdida de datos.

**Non-Goals:**
- Borrar cuentas o datos.
- Desactivar perfiles por inactividad individual.
- Usar actividad de workers, solicitudes de recursos estáticos o procesos internos como actividad humana.

## Decisions

- Mantener una fecha de última actividad autenticada en la cuenta. Actualizarla en solicitudes de aplicación de una sesión válida, con exclusiones para recursos estáticos y peticiones internas; no usar solo `last_login`, porque una sesión activa puede tener uso posterior al inicio de sesión.
- Ejecutar una tarea diaria que desactive aspirantes cuyo último uso (o fecha de creación/última activación si nunca iniciaron sesión) sea anterior al límite de siete días.
- Aplicar la desactivación mediante el mismo estado de acceso existente y registrar un motivo automático para que administración pueda distinguirlo de una decisión manual.
- Al reactivar, conservar todos los datos y establecer una nueva referencia de actividad en el momento de la reactivación.
- Implementar este cambio después de `mensaje-y-control-cuenta-inactiva`, que añade una explicación de bloqueo al iniciar sesión.

## Risks / Trade-offs

- [Una petición automática de la interfaz podría contar como actividad] → Excluir endpoints de sondeo y tráfico técnico que no represente uso de la persona.
- [Una medición demasiado estricta puede desactivar a alguien que usa una sola pantalla durante largo tiempo] → Actualizar la fecha de actividad en interacciones autenticadas ordinarias de la aplicación y revisar la ventana de sesión.
- [El job diario puede ejecutarse más de una vez] → Hacer idempotente la desactivación y auditar solo el cambio efectivo.

## Migration Plan

- Para cuentas existentes sin fecha de actividad registrada, inicializar el valor a la última fecha de inicio de sesión disponible; si no existe, usar su fecha de creación o activación.
- Desplegar primero captura de actividad y mensaje de cuenta inactiva; habilitar el job automático una vez que la ruta manual de reactivación esté disponible.
- Revertir deshabilitando el job automático; no reactivar en masa cuentas desactivadas ni borrar su motivo/historial.
