# Tasks

## 1. Crear y administrar invitaciones

- [x] 1.1 Añadir persistencia de invitaciones con token no reversible, correo destinatario, vencimiento, uso y revocación; verificar migración sin modificar cuentas existentes ni registrar tokens en auditoría.
- [x] 1.2 Añadir al panel de usuarios la opción de generar, copiar y revocar invitaciones sin retirar el alta directa existente; verificar permisos administrativos, enlace mostrado una sola vez y revocación del enlace anterior.

## 2. Aceptar invitaciones

- [x] 2.1 Añadir la página pública de aceptación que valide el enlace y permita definir usuario y contraseña asociados al correo invitado; verificar que la cuenta creada no obtiene privilegios administrativos.
- [x] 2.2 Consumir la invitación atómicamente al crear la cuenta y conservarla cuando falle la validación del formulario; verificar uso único, concurrencia, expiración, revocación y usuario duplicado.
- [x] 2.3 Mantener cerrado el registro sin invitación válida y actualizar las pruebas de gestión de usuarios para cubrir el nuevo flujo completo.
