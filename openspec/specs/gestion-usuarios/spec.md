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

### Requirement: Proteger acciones de gestión de usuarios
El sistema SHALL autorizar cada operación de consulta o gestión de cuentas según los privilegios de administración.

#### Scenario: Una cuenta no administrativa solicita una acción de gestión
- **WHEN** una cuenta aspirante solicita listar usuarios o iniciar un restablecimiento para otra cuenta
- **THEN** el sistema deniega la operación sin revelar si la cuenta objetivo existe
