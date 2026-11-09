# Proposal

## Why

La administración actualmente crea cuentas directamente y debe manejar credenciales iniciales. Un enlace de invitación permite que la persona complete su propia cuenta sin abrir el registro público ni compartir una contraseña inicial.

## What Changes

- Añadir a la gestión actual la opción de generar una invitación única asociada al correo de la persona invitada.
- Mostrar el enlace una sola vez para que la administración lo copie y lo envíe por su canal habitual.
- Permitir que el invitado defina su usuario y contraseña al aceptar el enlace.
- Expirar las invitaciones no usadas a los siete días, permitir revocarlas y rechazar enlaces vencidos o ya utilizados.
- Mantener cerrado el auto-registro público sin invitación válida.

## Capabilities

### New Capabilities

### Modified Capabilities
- `cuentas-y-perfiles`: sumar un flujo de invitación de un solo uso a la gestión existente, sin habilitar auto-registro público.

## Impact

- Gestión administrativa de cuentas y formulario público de aceptación de invitación.
- Almacenamiento del estado, vencimiento y consumo de invitaciones; no requiere envío automático de correo.
