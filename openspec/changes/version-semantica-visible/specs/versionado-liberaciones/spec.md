# Spec Delta

## MODIFIED Requirements

### Requirement: Mostrar la versión del artefacto desplegado
La interfaz SHALL mostrar en el pie de página la versión SemVer declarada en el archivo `VERSION` del código de la aplicación que está ejecutándose, tanto en staging como en producción. El SHA y el digest SHALL permanecer como metadatos técnicos y no SHALL mostrarse como versión de producto.

#### Scenario: La aplicación ejecuta una liberación de producción
- **WHEN** una persona consulta cualquier pantalla de una versión desplegada en producción
- **THEN** el pie de página muestra la versión semántica inmutable de esa liberación

#### Scenario: La versión canónica llega a producción
- **WHEN** el pipeline promueve a producción el artefacto probado en staging
- **THEN** toma la versión semántica del archivo `VERSION` del código de la liberación y la muestra sin reconstruir la imagen

#### Scenario: La aplicación ejecuta una imagen de staging
- **WHEN** una persona autorizada consulta una pantalla de staging
- **THEN** el pie de página muestra la versión SemVer declarada en `VERSION` para el código de esa imagen y no muestra el SHA ni el digest

#### Scenario: No hay una versión SemVer válida disponible
- **WHEN** el artefacto no incluye una versión SemVer válida en `VERSION`
- **THEN** la interfaz indica que la versión no está disponible y no muestra un valor fijo, un SHA o un digest como sustituto
