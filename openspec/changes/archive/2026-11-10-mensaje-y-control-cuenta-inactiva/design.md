# Design

## Context

La especificación `cuentas-y-perfiles` ya contempla la activación y desactivación manual de cuentas por la administración, y `gestion-usuarios` ya contempla mostrar su estado. Falta un resultado específico en el inicio de sesión para credenciales válidas de una cuenta desactivada.

## Goals / Non-Goals

**Goals:**
- Explicar el bloqueo a una persona que demuestra conocer las credenciales de una cuenta inactiva.
- Mantener la respuesta genérica para credenciales inválidas y así no revelar el estado de cuentas a terceros.

**Non-Goals:**
- Cambiar el control administrativo existente de activación/desactivación.
- Enviar notificaciones o correos automáticos.
- Permitir que la persona reactive su cuenta sin intervención administrativa.

## Decisions

- Diferenciar la respuesta solo cuando la autenticación identifica credenciales válidas de una cuenta inactiva; para credenciales incorrectas se conserva el error genérico.
- Mostrar un mensaje directo que indique contactar a la administración, sin exponer detalles internos o el motivo específico de desactivación.
- La reactivación se realiza desde la consola existente; al volver a habilitar la cuenta, el flujo normal de inicio de sesión vuelve a aplicar.

## Risks / Trade-offs

- [La respuesta puede revelar que la cuenta existe] → Solo mostrarla después de validar la contraseña correcta; las credenciales erróneas conservan el mensaje genérico.

## Migration Plan

- No requiere migrar datos ni cambiar cuentas existentes.
- Si se revierte, el inicio de sesión vuelve al mensaje genérico para todas las cuentas que no puedan autenticarse.
