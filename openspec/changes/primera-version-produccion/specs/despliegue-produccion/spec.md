# Spec Delta

## Purpose

Operar Ramper Job en producción con recursos y datos separados de staging y promover únicamente el artefacto ya validado.

## ADDED Requirements

### Requirement: Aislar el entorno productivo
Producción SHALL usar recursos, configuración, credenciales, base de datos y archivos privados propios, separados de staging.

#### Scenario: Se prepara producción
- **WHEN** Flux reconcilia la aplicación en producción
- **THEN** los recursos se crean en `prod` y usan Secrets distintos a los de staging

#### Scenario: Se configura el acceso externo
- **WHEN** una persona abre la aplicación productiva
- **THEN** el host `jobs.ramper.lat` sirve la aplicación y protege los CV con autenticación

#### Scenario: Se configura OmniRoute
- **WHEN** producción analiza una vacante
- **THEN** usa OmniRoute interno de producción y no el endpoint público de staging

### Requirement: Promover el artefacto validado en staging
Una liberación productiva SHALL usar exactamente el SHA o digest validado en staging y SHALL quedar bajo reconciliación GitOps desde `main`.

#### Scenario: Se aprueba una liberación
- **WHEN** se aprueba el candidato probado en staging
- **THEN** producción usa la misma imagen inmutable y Flux obtiene el overlay desde `main`

#### Scenario: Faltan Secrets
- **WHEN** se prepara la fuente Flux de producción pero faltan Secrets de app o GHCR
- **THEN** la Kustomization permanece suspendida y no crea los recursos de Ramper Job

### Requirement: Crear acceso administrativo inicial
El sistema SHALL permitir provisionar una sola cuenta administradora inicial sin registrar públicamente cuentas ni revelar su contraseña.

#### Scenario: Primer administrador
- **WHEN** se ejecuta el bootstrap con contraseña interactiva y oculta
- **THEN** crea la cuenta y la contraseña no aparece en argumentos, archivos, historial ni logs

#### Scenario: Segundo administrador
- **WHEN** ya existe un administrador
- **THEN** el bootstrap rechaza crear otro

### Requirement: Operar sin backups
Ramper Job SHALL NOT configurar copias de seguridad de PostgreSQL o CV en producción; la información SHALL considerarse susceptible de pérdida irreversible.

#### Scenario: Se pierde nodo o PVC
- **WHEN** se pierde el nodo o un PVC productivo
- **THEN** se acepta que no hay restauración desde backup

### Requirement: Validar la liberación
Una versión SHALL considerarse disponible solo cuando web, worker y Beat estén listos, el administrador pueda iniciar sesión y la privacidad de CV funcione.

#### Scenario: Validación inicial
- **WHEN** termina el despliegue
- **THEN** se comprueban salud, login, OmniRoute, aislamiento de datos y descarga privada de CV antes de invitar familiares
