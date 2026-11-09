# Design

## Context

La gestión de usuarios ya solicita recuperaciones para cuentas activas y usa los formularios de restablecimiento de Django para enviar un enlace por correo. La aplicación cuenta con tokens de un solo uso, vencimiento configurable y auditoría administrativa.

## Goals / Non-Goals

**Goals:**
- Dejar que el admin copie y comparta manualmente el enlace generado para la cuenta elegida.
- Reutilizar el vencimiento y la confirmación segura de contraseña existentes.
- Evitar guardar o registrar el token en claro.

**Non-Goals:**
- Enviar el enlace automáticamente por correo en este flujo.
- Permitir que el administrador establezca, vea o comparta directamente la nueva contraseña.
- Cambiar el formulario público de recuperación por correo, si se habilita para otros casos.

## Decisions

### Reutilizar el token y la confirmación de Django

Generar el token para la cuenta seleccionada con el mecanismo de restablecimiento vigente y construir la URL absoluta de confirmación. La ruta actual continúa validando la expiración y vuelve inválido el token después de cambiar la contraseña. El admin ve el enlace una sola vez en una respuesta protegida y puede copiarlo; no se invoca el envío automático de correo.

**Alternativa considerada:** crear un token y una página de cambio de contraseña propios. Se descarta porque duplicaría validación de expiración y consumo que el flujo de autenticación ya maneja.

### Mantener la auditoría sin el secreto

Registrar quién solicita el enlace y para qué cuenta, pero nunca la URL ni el token. Los errores y mensajes administrativos describen el resultado sin incluir credenciales.

**Alternativa considerada:** guardar el enlace en el historial del admin para consultarlo luego. Se descarta porque conservaría un secreto de acceso reutilizable fuera de la vista de confirmación.

## Risks / Trade-offs

- [El enlace puede ser copiado o compartido incorrectamente] → Mostrar claramente la cuenta destinataria y limitar la presentación del enlace al admin autenticado.
- [El navegador o infraestructura puede registrar la URL] → No incluir el token en logs, analítica ni auditoría; mantener el flujo en HTTPS en los entornos desplegados.
- [El admin pierde el enlace después de cerrar la vista] → Permitir generar uno nuevo; cada solicitud queda auditada y no se conserva el anterior en pantalla.

## Migration Plan

1. Cambiar la acción administrativa para generar el enlace y presentarlo para copia sin invocar la entrega por correo.
2. Mantener la vista de confirmación, las validaciones de contraseña y el vencimiento existentes.
3. Verificar token válido, token vencido/usado, cuenta inactiva, usuario no administrador, auditoría y ausencia del token en logs y eventos.
