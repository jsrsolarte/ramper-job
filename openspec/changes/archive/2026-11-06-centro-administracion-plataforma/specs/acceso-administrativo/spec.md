# Spec Delta

## Purpose

Define el acceso de administración de la plataforma y su centro protegido, desde el que la única persona administradora puede llegar a los tableros operativos y herramientas de gestión.

## ADDED Requirements

### Requirement: Mantener una sola cuenta administradora
El sistema SHALL permitir como máximo una cuenta con privilegios de administración de plataforma.

#### Scenario: Se configura la cuenta administradora
- **WHEN** se provisiona la cuenta administrativa inicial
- **THEN** el sistema permite el acceso administrativo a esa cuenta sin habilitar el auto-registro público de administradores

#### Scenario: Se intenta crear otra cuenta administradora
- **WHEN** una operación intenta asignar privilegios de administración a una segunda cuenta
- **THEN** el sistema rechaza la operación y conserva la cuenta administradora existente

### Requirement: Restringir el centro administrativo
El sistema SHALL permitir acceder al centro y a sus datos únicamente a la cuenta administradora autorizada.

#### Scenario: La persona administradora abre el centro
- **WHEN** la cuenta administradora autenticada solicita el centro administrativo
- **THEN** el sistema presenta las herramientas y vistas administrativas disponibles

#### Scenario: Una cuenta aspirante intenta abrir el centro
- **WHEN** una cuenta sin privilegios administrativos solicita el centro o un endpoint administrativo
- **THEN** el sistema deniega el acceso sin revelar datos ni ejecutar acciones administrativas

### Requirement: Integrar las vistas operativas existentes
El centro administrativo SHALL ofrecer navegación a los tableros operativos disponibles sin duplicar sus métricas ni cambiar sus reglas de acceso.

#### Scenario: El tablero operativo está disponible
- **WHEN** la persona administradora consulta el centro
- **THEN** puede abrir el tablero de observabilidad de ingesta y análisis desde la navegación administrativa
