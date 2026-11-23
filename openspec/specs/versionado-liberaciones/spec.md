# Versionado de liberaciones Specification

## Purpose

Define cómo identificar cada versión publicada de Ramper Job y relacionarla de forma inequívoca con el código y la imagen desplegados.

## Requirements

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
El sistema SHALL relacionar cada versión de producción con una etiqueta inmutable, el SHA del commit fuente y el digest de la imagen publicada, y SHALL desplegar exactamente el artefacto validado en staging.

#### Scenario: Se publica una versión a producción
- **WHEN** una versión se integra a `main` después de validarse en staging
- **THEN** su etiqueta, SHA y digest identifican el mismo código y la misma imagen que se probaron en staging

#### Scenario: Se prepara una prueba de staging
- **WHEN** se construye una imagen de staging desde una rama o commit candidato
- **THEN** se identifica por SHA o digest sin consumir ni asignar una versión de producción

#### Scenario: Se intenta reutilizar una etiqueta de versión
- **WHEN** una etiqueta de versión ya existe
- **THEN** el sistema rechaza moverla o reutilizarla para otro commit o imagen


### Requirement: Mostrar la versión del artefacto desplegado
La interfaz SHALL mostrar en el pie de página común un identificador que corresponda al artefacto de la aplicación que está ejecutándose.

#### Scenario: La aplicación ejecuta una liberación de producción
- **WHEN** una persona consulta cualquier pantalla de una versión desplegada en producción
- **THEN** el pie de página muestra la versión semántica inmutable de esa liberación

#### Scenario: La versión canónica llega a producción
- **WHEN** el pipeline promueve a producción el artefacto probado en staging
- **THEN** toma la versión semántica del archivo `VERSION` del código de la liberación y la muestra sin reconstruir la imagen

#### Scenario: La aplicación ejecuta una imagen de staging
- **WHEN** una persona autorizada consulta una pantalla de staging
- **THEN** el pie de página muestra el SHA o identificador del commit de la imagen, sin presentarlo como versión de producción

#### Scenario: No hay metadatos de versión disponibles
- **WHEN** la aplicación no puede determinar el identificador del artefacto en ejecución
- **THEN** la interfaz indica que la versión no está disponible y no muestra un valor fijo o desactualizado