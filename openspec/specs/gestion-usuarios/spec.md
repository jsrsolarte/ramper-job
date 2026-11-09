# gestion-usuarios Specification

## Purpose

Permite que la persona administradora consulte y mantenga las cuentas de aspirantes, y que ayude a recuperar el acceso sin conocer las contraseñas de otras personas.

## Requirements

### Requirement: Consultar las cuentas de usuarios
El centro administrativo SHALL permitir a la persona administradora consultar las cuentas de aspirantes y su estado de acceso.

#### Scenario: La persona administradora consulta usuarios
- **WHEN** la persona administradora abre la gestión de usuarios
- **THEN** el sistema muestra las cuentas de aspirantes y si cada una está activa o desactivada

### Requirement: Restablecer la contraseña de una cuenta
El sistema SHALL permitir que la persona administradora inicie un restablecimiento de contraseña sin consultar ni mostrar la contraseña actual o nueva.

#### Scenario: Se solicita restablecer el acceso
- **WHEN** la persona administradora solicita restablecer la contraseña de un aspirante
- **THEN** el sistema genera un proceso seguro de recuperación y no revela la contraseña a la persona administradora

#### Scenario: El enlace o código de recuperación expiró
- **WHEN** una persona intenta completar el restablecimiento con un enlace o código vencido o ya utilizado
- **THEN** el sistema rechaza la operación y requiere una nueva solicitud de recuperación

### Requirement: Compartir manualmente un enlace de restablecimiento
El sistema SHALL permitir que la persona administradora genere para una cuenta activa un enlace de restablecimiento de un solo uso, válido por el plazo de expiración configurado, y compartirlo manualmente sin consultar ni mostrar la contraseña actual o nueva.

#### Scenario: Administrador genera un enlace de restablecimiento
- **WHEN** la persona administradora solicita restablecer la contraseña de un aspirante activo
- **THEN** el sistema genera un enlace vinculado a esa cuenta y lo muestra una sola vez para que la administración lo copie

#### Scenario: Administrador comparte el enlace
- **WHEN** se genera un enlace correctamente
- **THEN** el sistema no envía un correo automáticamente y no muestra ni revela la contraseña al administrador

#### Scenario: Usuario completa el restablecimiento
- **WHEN** el aspirante abre el enlace vigente y establece una contraseña válida
- **THEN** el sistema actualiza su contraseña y el enlace deja de ser válido

#### Scenario: El enlace expiró o ya se utilizó
- **WHEN** una persona intenta completar el restablecimiento con un enlace vencido o ya utilizado
- **THEN** el sistema rechaza la operación y requiere que la administración genere un nuevo enlace

#### Scenario: El enlace no se expone en registros
- **WHEN** se genera, muestra o consume un enlace de restablecimiento
- **THEN** el token no se guarda en auditoría ni se escribe en logs

### Requirement: Proteger acciones de gestión de usuarios
El sistema SHALL autorizar cada operación de consulta o gestión de cuentas según los privilegios de administración.

#### Scenario: Una cuenta no administrativa solicita una acción de gestión
- **WHEN** una cuenta aspirante solicita listar usuarios o iniciar un restablecimiento para otra cuenta
- **THEN** el sistema deniega la operación sin revelar si la cuenta objetivo existe
