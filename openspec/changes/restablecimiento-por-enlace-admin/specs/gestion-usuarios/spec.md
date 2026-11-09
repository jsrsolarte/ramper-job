# Spec Delta

## ADDED Requirements

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
