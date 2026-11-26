# Proposal

## Why

Las cuentas que llevan tiempo sin usar la plataforma no deberían seguir contando como activas indefinidamente. Una política global de inactividad permite mantener el acceso ordenado y liberar trabajo automático para quienes sí utilizan el servicio.

## What Changes

- Desactivar automáticamente cuentas de aspirantes tras siete días consecutivos sin actividad autenticada.
- Conservar los datos, historial y perfiles de las cuentas desactivadas.
- Excluir la cuenta administradora y permitir reactivar las cuentas desde la consola.
- Requerir primero el cambio `mensaje-y-control-cuenta-inactiva`, para que la persona sepa cómo recuperar el acceso.

## Capabilities

### New Capabilities

### Modified Capabilities
- `cuentas-y-perfiles`: añadir la desactivación automática por inactividad al ciclo de vida de las cuentas.

## Impact

- Seguimiento de actividad de cuentas autenticadas.
- Proceso periódico de mantenimiento de cuentas.
- Inicio de sesión y consola de gestión de usuarios.
