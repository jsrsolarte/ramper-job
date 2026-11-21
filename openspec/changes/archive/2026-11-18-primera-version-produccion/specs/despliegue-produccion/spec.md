# Spec Delta

## Purpose

Permite operar Ramper Job en producción con recursos, credenciales y datos separados de staging, y liberar únicamente código de aplicación validado en staging.

## ADDED Requirements

### Requirement: Aislar el entorno productivo
Producción SHALL usar recursos, configuración, credenciales, base de datos y archivos privados propios, separados de staging.

#### Scenario: Se prepara producción
- **WHEN** Flux reconcilia la aplicación en producción
- **THEN** los recursos se crean en `prod` y usan Secrets distintos a los de staging

#### Scenario: Se configura el acceso externo
- **WHEN** una persona abre la aplicación productiva
- **THEN** el host `jobs.ramper.lat` sirve la aplicación y protege los archivos CV con autenticación

#### Scenario: Se configura OmniRoute
- **WHEN** producción analiza una vacante
- **THEN** usa el servicio OmniRoute configurado para producción y no la URL pública de staging

### Requirement: Liberar en producción el código validado en staging
Una liberación productiva SHALL partir del código de aplicación aprobado en staging e integrado en `main` mediante PR, y SHALL quedar bajo reconciliación GitOps desde `main`. El merge puede generar otro SHA y el pipeline puede construir otra imagen; la relación con el código aprobado debe quedar comprobada.

#### Scenario: Se integra una versión probada
- **WHEN** el código aprobado en staging se integra en `main`
- **THEN** se dispara el pipeline de producción y, tras autorización explícita, Flux despliega la versión desde el overlay de `main`

#### Scenario: El merge crea otro commit
- **WHEN** el PR genera un SHA de merge distinto al candidato probado en staging
- **THEN** el pipeline verifica que el código de aplicación integrado corresponde al candidato aprobado y registra ambos SHA

#### Scenario: No están provisionados los Secrets
- **WHEN** se prepara la fuente Flux de producción pero faltan los Secrets de la aplicación o GHCR
- **THEN** la reconciliación productiva permanece suspendida y no crea los recursos de Ramper Job

### Requirement: Crear el acceso administrativo inicial de producción
El sistema SHALL permitir provisionar una sola cuenta administradora inicial en producción sin registrar públicamente cuentas ni revelar la contraseña.

#### Scenario: Se crea el primer administrador
- **WHEN** la administración ejecuta el bootstrap en producción con una contraseña ingresada de forma interactiva y oculta
- **THEN** se crea una cuenta administradora y su contraseña no aparece en argumentos, archivos, historial ni logs

#### Scenario: Se intenta crear un segundo administrador
- **WHEN** ya existe una cuenta administradora en producción
- **THEN** el bootstrap rechaza crear otra cuenta

### Requirement: Operar producción sin backups
Ramper Job SHALL NOT configurar copias de seguridad de PostgreSQL o CV en producción; toda información almacenada SHALL considerarse susceptible de pérdida irreversible.

#### Scenario: Se pierde el nodo o un volumen
- **WHEN** el nodo o un PVC productivo se pierde
- **THEN** se acepta que la base, las cuentas, el historial y los CV no puedan recuperarse desde un backup

### Requirement: Validar la liberación productiva
Una versión SHALL considerarse disponible solo cuando web, worker y Beat estén listos, la cuenta administradora pueda iniciar sesión y los controles de acceso a CV funcionen.

#### Scenario: Se valida el flujo productivo
- **WHEN** termina el despliegue inicial
- **THEN** se comprueban salud, login, análisis con OmniRoute, aislamiento de datos y descarga privada de CV antes de invitar a familiares
