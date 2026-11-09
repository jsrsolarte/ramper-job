# Design

## Context

La gestión actual permite a la administración crear directamente una cuenta con usuario, correo y contraseña. El registro público no está habilitado. La aplicación ya tiene autenticación de Django y validación de contraseñas.

## Goals / Non-Goals

**Goals:**
- Dejar que la persona invitada establezca su contraseña y usuario.
- Mantener el alta cerrada a invitaciones creadas por la cuenta administradora.
- Permitir compartir el enlace manualmente sin activar correo saliente.

**Non-Goals:**
- Habilitar el registro público general.
- Permitir que una invitación otorgue permisos administrativos.
- Cambiar el flujo de restablecimiento de contraseña, que se especifica por separado.

## Decisions

### Guardar invitaciones revocables de un solo uso

Crear un registro de invitación asociado al correo destinatario, creador, fecha de expiración, fecha de uso y revocación. El enlace usa un token aleatorio de alta entropía; guardar solo su hash y mostrar el enlace completo una sola vez. La aceptación consume la invitación de forma atómica junto con la creación de cuenta, para que dos solicitudes simultáneas no puedan utilizarla. La invitación se agrega a la gestión actual y no elimina la opción de creación directa.

**Alternativa considerada:** generar un enlace firmado sin guardar estado. Se descarta porque no permite revocar un enlace ni invalidar el anterior al reemplazarlo.

### Validar el correo y las credenciales al aceptar

El correo se define al crear la invitación y se asocia a la cuenta aceptada. La persona invitada elige su nombre de usuario y contraseña; se aplican las validaciones y la política de contraseñas existentes. Un error del formulario no consume la invitación.

**Alternativa considerada:** dejar que quien reciba el enlace elija cualquier correo. Se descarta porque la invitación individual perdería su asociación con la persona destinataria.

### Exponer el enlace solo a administración

La página administrativa muestra el enlace de invitación recién generado una sola vez, con una acción para copiarlo. No se vuelve a mostrar en listados ni se escribe el token en logs o eventos de auditoría. Para reemplazar un enlace, la administración revoca el anterior y crea uno nuevo.

**Alternativa considerada:** enviar el enlace automáticamente por correo. Se descarta para este alcance porque la persona administradora quiere enviarlo por su canal habitual.

## Risks / Trade-offs

- [El enlace puede ser compartido con otra persona] → Asociarlo al correo destinatario, limitarlo a un uso y vencerlo a los siete días.
- [El enlace se puede exponer en logs o analítica del navegador] → No registrar URLs con tokens, evitar recursos externos en la página de aceptación y limpiar el token de la navegación después de validarlo.
- [Dos solicitudes pueden intentar consumirlo a la vez] → Validar, crear la cuenta y marcar la invitación consumida dentro de una transacción con bloqueo.

## Migration Plan

1. Añadir el almacenamiento de invitaciones y mantener intactas las cuentas existentes.
2. Añadir al panel de usuarios la generación de invitaciones sin retirar el formulario administrativo de creación directa.
3. Añadir la página de aceptación y mantener el registro sin invitación cerrado.
4. Verificar invitación válida, expirada, revocada, usada, reemplazada, usuario duplicado y concurrencia de aceptación.
