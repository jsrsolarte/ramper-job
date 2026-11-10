# Spec Delta

## ADDED Requirements

### Requirement: Informar el motivo de acceso denegado a una cuenta inactiva
El sistema SHALL indicar a una persona con credenciales válidas que su cuenta está inactiva y que debe contactar a la administración para recuperar el acceso.

#### Scenario: Una cuenta inactiva envía credenciales válidas
- **WHEN** una persona intenta iniciar sesión con el usuario y contraseña correctos de una cuenta desactivada
- **THEN** el sistema deniega el acceso e informa que la cuenta está inactiva y que debe contactar al administrador

#### Scenario: Una cuenta inactiva envía credenciales incorrectas
- **WHEN** una persona intenta iniciar sesión con credenciales incorrectas asociadas a una cuenta inactiva
- **THEN** el sistema muestra el mensaje genérico de credenciales inválidas y no revela el estado de la cuenta

#### Scenario: La cuenta se reactiva desde administración
- **WHEN** la persona administradora reactiva una cuenta previamente inactiva
- **THEN** la persona puede iniciar sesión con sus credenciales vigentes y deja de ver el mensaje de cuenta inactiva
