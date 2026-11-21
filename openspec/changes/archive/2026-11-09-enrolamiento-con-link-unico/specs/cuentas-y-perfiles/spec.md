# Spec Delta

## ADDED Requirements

### Requirement: Enrolar aspirantes mediante invitaciones
El sistema SHALL permitir que la persona administradora invite aspirantes con enlaces individuales de un solo uso, manteniendo cerrado el auto-registro público sin invitación válida.

#### Scenario: Administrador genera una invitación
- **WHEN** la persona administradora crea una invitación e indica el correo de la persona destinataria
- **THEN** el sistema genera un enlace único válido durante siete días, asociado a ese correo, y todavía no crea una cuenta

#### Scenario: Administrador comparte el enlace
- **WHEN** se genera una invitación correctamente
- **THEN** el sistema muestra el enlace una sola vez para que la administración lo copie y lo envíe por su canal habitual, sin enviar un correo automáticamente

#### Scenario: Invitado completa su cuenta
- **WHEN** la persona destinataria abre una invitación vigente y proporciona un usuario y contraseña válidos
- **THEN** el sistema crea una cuenta individual activa asociada al correo de la invitación y consume el enlace

#### Scenario: Invitación inválida, vencida, revocada o utilizada
- **WHEN** una persona intenta aceptar una invitación que no existe, venció, fue revocada o ya se utilizó
- **THEN** el sistema no crea la cuenta y ofrece solicitar una nueva invitación a la administración

#### Scenario: El formulario de invitación tiene errores
- **WHEN** una persona envía un usuario repetido o una contraseña inválida usando una invitación todavía vigente
- **THEN** el sistema muestra los errores y conserva la invitación disponible hasta su vencimiento o aceptación exitosa

#### Scenario: La persona intenta auto-registrarse con invitación
- **WHEN** una persona intenta crear una cuenta sin una invitación válida
- **THEN** el sistema no permite crear la cuenta

#### Scenario: Administrador revoca o reemplaza una invitación
- **WHEN** la persona administradora revoca una invitación pendiente o genera un reemplazo
- **THEN** el enlace revocado o reemplazado deja de permitir el registro

#### Scenario: Administrador desactiva una cuenta
- **WHEN** la persona administradora desactiva la cuenta de un aspirante
- **THEN** el sistema revoca su acceso sin eliminar su historial ni sus datos asociados

#### Scenario: Administrador reactiva una cuenta
- **WHEN** la persona administradora reactiva una cuenta previamente desactivada
- **THEN** el sistema permite que esa persona vuelva a iniciar sesión y conserva su información existente
