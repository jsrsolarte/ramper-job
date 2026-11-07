# Spec Delta

## Purpose

Evita mostrar varias veces la misma vacante de una bolsa cuando aparece en consultas distintas o se publica con variaciones de URL.

## ADDED Requirements

### Requirement: Reconocer una vacante repetida dentro de una bolsa
El sistema SHALL identificar una vacante por bolsa usando su identificador estable cuando esté disponible y, de lo contrario, una huella normalizada de sus datos principales.

#### Scenario: El mismo identificador aparece con otra URL
- **WHEN** una bolsa entrega de nuevo una vacante con el mismo identificador y una URL distinta
- **THEN** el sistema actualiza el registro existente y presenta una sola vacante

#### Scenario: No hay identificador estable
- **WHEN** se ingresa una vacante sin identificador estable cuyos datos normalizados de cargo, empresa y ubicación coinciden con otra de la misma bolsa
- **THEN** el sistema conserva un único registro de vacante

#### Scenario: Vacantes de bolsas distintas
- **WHEN** dos bolsas ofrecen vacantes con datos coincidentes
- **THEN** cada bolsa conserva su propio registro

### Requirement: Mantener análisis al consolidar vacantes repetidas
El sistema SHALL mantener los análisis de perfiles asociados a una vacante cuando consolida registros repetidos de esa misma vacante.

#### Scenario: Consolidar registros previamente almacenados
- **WHEN** una migración encuentra vacantes duplicadas con análisis asociados
- **THEN** los análisis que no estén repetidos quedan vinculados al registro conservado y el dashboard no muestra duplicados del mismo análisis
