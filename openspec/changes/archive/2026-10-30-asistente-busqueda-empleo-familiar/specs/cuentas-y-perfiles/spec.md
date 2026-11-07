# Spec Delta

## Purpose

Permite que cada familiar use una cuenta administrada para mantener su información de búsqueda laboral y consultar únicamente sus propios resultados.

## ADDED Requirements

### Requirement: Cuentas administradas
El sistema SHALL permitir que una persona administradora cree y desactive cuentas de familiares, sin habilitar el auto-registro público.

#### Scenario: Administrador crea una cuenta
- **WHEN** la persona administradora registra una cuenta para un familiar
- **THEN** el sistema crea el acceso individual y permite que esa persona inicie sesión

#### Scenario: Persona intenta auto-registrarse
- **WHEN** una persona sin cuenta intenta registrarse desde el acceso público
- **THEN** el sistema no permite crear una cuenta

### Requirement: Aislamiento de información por cuenta
El sistema SHALL mostrar a cada familiar solo sus propios CV, criterios de búsqueda y vacantes analizadas.

#### Scenario: Persona consulta su dashboard
- **WHEN** una persona autenticada abre su dashboard
- **THEN** el sistema muestra únicamente su información y resultados

#### Scenario: Persona intenta consultar información ajena
- **WHEN** una persona autenticada solicita información asociada a otra cuenta
- **THEN** el sistema deniega el acceso y no revela esa información

### Requirement: CV y criterios de búsqueda
El sistema SHALL permitir a cada persona cargar o actualizar su CV y definir criterios para orientar la búsqueda de vacantes.

#### Scenario: Persona actualiza su perfil
- **WHEN** la persona guarda un CV o cambia sus criterios de búsqueda
- **THEN** el sistema conserva la versión vigente para las siguientes búsquedas y análisis

#### Scenario: Se actualiza un perfil ya analizado
- **WHEN** la persona modifica su CV o sus criterios de búsqueda
- **THEN** los análisis existentes conservan la referencia a la versión del perfil con la que se generaron y los análisis posteriores usan la versión vigente
