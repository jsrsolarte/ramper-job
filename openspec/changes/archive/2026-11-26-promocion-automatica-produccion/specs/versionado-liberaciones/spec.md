# Spec Delta

## MODIFIED Requirements

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
