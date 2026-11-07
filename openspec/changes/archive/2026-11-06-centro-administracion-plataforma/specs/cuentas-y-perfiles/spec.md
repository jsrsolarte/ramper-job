# Spec Delta

## MODIFIED Requirements

### Requirement: Cuentas administradas
El sistema SHALL permitir que la única persona administradora cree, desactive y reactive cuentas de familiares, sin habilitar el auto-registro público.

#### Scenario: Administrador crea una cuenta
- **WHEN** la persona administradora registra una cuenta para un familiar
- **THEN** el sistema crea el acceso individual y permite que esa persona inicie sesión

#### Scenario: Persona intenta auto-registrarse
- **WHEN** una persona sin cuenta intenta registrarse desde el acceso público
- **THEN** el sistema no permite crear una cuenta

#### Scenario: Administrador desactiva una cuenta
- **WHEN** la persona administradora desactiva la cuenta de un familiar
- **THEN** el sistema revoca su acceso sin eliminar su historial ni sus datos asociados

#### Scenario: Administrador reactiva una cuenta
- **WHEN** la persona administradora reactiva una cuenta previamente desactivada
- **THEN** el sistema permite que esa persona vuelva a iniciar sesión y conserva su información existente
