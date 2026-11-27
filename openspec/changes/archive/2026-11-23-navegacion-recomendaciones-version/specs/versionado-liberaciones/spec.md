# Spec Delta

## ADDED Requirements

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
