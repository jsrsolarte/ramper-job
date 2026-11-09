# Spec Delta

## Purpose

Define cómo identificar cada versión publicada de Ramper Job y relacionarla de forma inequívoca con el código y la imagen desplegados.

## ADDED Requirements

### Requirement: Asignar versiones semánticas a lanzamientos de producción
Cada lanzamiento aprobado a producción SHALL recibir una versión `MAJOR.MINOR.PATCH`; la primera liberación de producción SHALL ser `1.0.0`.

#### Scenario: Primera liberación de producción
- **WHEN** se aprueba la primera promoción de Ramper Job a producción
- **THEN** la aplicación se libera como versión `1.0.0`

#### Scenario: Corrección compatible
- **WHEN** se publica una versión que contiene únicamente correcciones compatibles con la versión anterior
- **THEN** se incrementa PATCH y se mantienen MAJOR y MINOR

#### Scenario: Funcionalidad compatible
- **WHEN** se publica funcionalidad compatible con los contratos existentes
- **THEN** se incrementa MINOR y PATCH vuelve a cero

#### Scenario: Cambio incompatible
- **WHEN** se publica un cambio incompatible que requiere adaptación de usuarios o integraciones
- **THEN** se incrementa MAJOR y MINOR y PATCH vuelven a cero

### Requirement: Asociar cada versión al artefacto liberado
El sistema SHALL relacionar cada versión de producción con una etiqueta inmutable, el SHA del commit fuente y el digest de la imagen publicada, y SHALL desplegar exactamente ese artefacto.

#### Scenario: Se publica una versión a producción
- **WHEN** una versión se aprueba para producción
- **THEN** su etiqueta, SHA y digest identifican el mismo código que se validó en staging

#### Scenario: Se prepara una prueba de staging
- **WHEN** se construye una imagen de staging desde una rama o commit candidato
- **THEN** se identifica por SHA o digest sin consumir ni asignar una versión de producción

#### Scenario: Se intenta reutilizar una etiqueta de versión
- **WHEN** una etiqueta de versión ya existe
- **THEN** el sistema rechaza moverla o reutilizarla para otro commit o imagen
