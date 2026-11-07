# Cuentas y perfiles Specification

## Purpose

Permite que cada familiar use una cuenta administrada para mantener su información de búsqueda laboral y consultar únicamente sus propios resultados.

## Requirements

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

### Requirement: Aislamiento de información por cuenta
El sistema SHALL mostrar a cada familiar solo sus propios CV, preferencias y vacantes analizadas.

#### Scenario: Persona consulta su dashboard
- **WHEN** una persona autenticada abre su dashboard
- **THEN** el sistema muestra únicamente su información y resultados

#### Scenario: Persona intenta consultar información ajena
- **WHEN** una persona autenticada solicita información asociada a otra cuenta
- **THEN** el sistema deniega el acceso y no revela esa información

### Requirement: CV y preferencias de búsqueda
El sistema SHALL permitir a cada persona cargar o actualizar su CV y definir preferencias que orienten sus búsquedas de vacantes.

#### Scenario: Persona actualiza su perfil
- **WHEN** la persona guarda un CV o cambia sus preferencias
- **THEN** el sistema conserva la revisión vigente para las siguientes búsquedas y análisis

#### Scenario: Se actualiza un perfil ya analizado
- **WHEN** la persona modifica su CV o sus preferencias
- **THEN** los análisis existentes conservan la referencia a la revisión con que se generaron y los análisis posteriores usan la revisión vigente

### Requirement: Descarga privada del CV
El sistema SHALL permitir la descarga del CV únicamente a su propietario autenticado.

#### Scenario: El propietario descarga su CV
- **WHEN** el aspirante autenticado solicita el archivo vigente de su perfil
- **THEN** el sistema entrega el archivo asociado a ese perfil

#### Scenario: Otra cuenta solicita el archivo
- **WHEN** una cuenta distinta o una persona no autenticada solicita el CV
- **THEN** el sistema no revela ni entrega el archivo
