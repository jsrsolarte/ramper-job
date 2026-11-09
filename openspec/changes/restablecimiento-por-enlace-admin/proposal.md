# Proposal

## Why

La administración ya puede iniciar una recuperación, pero el sistema envía el enlace directamente por correo y depende del correo saliente. Generar el enlace para que el admin lo copie y lo comparta manualmente permite entregar la recuperación por el canal acordado con cada persona.

## What Changes

- Permitir que el admin genere un enlace de restablecimiento asociado a una cuenta específica.
- Mostrar el enlace recién generado una sola vez para copiarlo y enviarlo manualmente.
- Mantener el enlace de un solo uso, con vencimiento, y no exponer la contraseña a la administración.
- Auditar la solicitud sin guardar ni registrar el token.

## Capabilities

### New Capabilities

### Modified Capabilities
- `gestion-usuarios`: generar y compartir manualmente un enlace de restablecimiento en lugar de depender del envío automático por correo.

## Impact

- Acción de restablecimiento en la gestión administrativa de usuarios.
- Página de confirmación de contraseña; el proceso deja de depender de correo saliente.
