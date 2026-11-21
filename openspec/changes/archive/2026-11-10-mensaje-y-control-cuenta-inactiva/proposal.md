# Proposal

## Why

La consola ya contempla activar y desactivar cuentas, pero una persona con la cuenta desactivada necesita entender por qué no puede ingresar y cómo recuperar el acceso. Un mensaje específico evita confundir el bloqueo con una contraseña incorrecta.

## What Changes

- Explicar el estado inactivo cuando una cuenta desactivada intenta iniciar sesión con credenciales correctas.
- Indicar que debe contactar a la administración para recuperar el acceso.
- Mantener la respuesta de autenticación genérica cuando las credenciales sean incorrectas.
- Reutilizar el control de activación/desactivación que ya está definido para la consola administrativa, evitando duplicar esa capacidad.

## Capabilities

### New Capabilities

### Modified Capabilities
- `gestion-usuarios`: definir el mensaje de acceso para cuentas inactivas.

## Impact

- Flujo de inicio de sesión.
- Gestión administrativa de usuarios ya existente.
