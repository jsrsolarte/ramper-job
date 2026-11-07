# Deduplicación de vacantes Specification

## Purpose

Evita mostrar varias veces la misma vacante de una bolsa cuando aparece en consultas distintas o con variaciones de URL.

## Requirements

### Requirement: Reconocer una vacante repetida dentro de una bolsa
El sistema SHALL identificar una vacante por bolsa usando su identificador estable cuando esté disponible y, de lo contrario, una huella normalizada de sus datos principales.

#### Scenario: El mismo identificador aparece con otra URL
- **WHEN** una bolsa entrega de nuevo una vacante con el mismo identificador y una URL distinta
- **THEN** el sistema actualiza el registro existente y presenta una sola vacante

#### Scenario: No hay identificador estable
- **WHEN** una vacante sin identificador tiene cargo, empresa y ubicación normalizados coincidentes con otra de la misma bolsa
- **THEN** el sistema conserva un solo registro

#### Scenario: Vacantes de bolsas distintas
- **WHEN** dos bolsas ofrecen vacantes con datos coincidentes
- **THEN** cada bolsa conserva su propio registro

### Requirement: Mantener análisis al consolidar vacantes repetidas
El sistema SHALL mantener los análisis de perfiles asociados al consolidar registros repetidos de una misma vacante.

#### Scenario: Consolidar registros previamente almacenados
- **WHEN** se consolidan vacantes duplicadas que tienen análisis asociados
- **THEN** los análisis no repetidos quedan vinculados al registro conservado y el dashboard no muestra duplicados del mismo análisis
