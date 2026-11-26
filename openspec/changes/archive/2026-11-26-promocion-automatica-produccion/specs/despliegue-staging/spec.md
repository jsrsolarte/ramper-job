# Spec Delta

## MODIFIED Requirements

### Requirement: Separar los pipelines de staging y producción
El sistema SHALL identificar por separado la validación de PR, la entrega a staging y el pipeline de producción activado por cambios integrados en `main`. La promoción a producción SHALL ocurrir automáticamente solo cuando el commit integrado contiene código de aplicación ya validado y publicado en staging.

#### Scenario: Se valida un cambio propuesto
- **WHEN** se abre o actualiza un PR de aplicación
- **THEN** CI ejecuta las validaciones correspondientes sin modificar el pin ni desplegar en ninguno de los entornos

#### Scenario: Se integra en main el código probado en staging
- **WHEN** se integra a `main` mediante PR un candidato ya validado y publicado en `staging`
- **THEN** el pipeline de producción valida el commit integrado y, si todas las verificaciones pasan, actualiza automáticamente el pin productivo al artefacto inmutable probado en staging

#### Scenario: El merge genera un SHA distinto
- **WHEN** el merge a `main` produce un SHA distinto al commit probado en `staging`
- **THEN** el pipeline verifica que el código de aplicación integrado corresponde al candidato aprobado y conserva el SHA y digest de la imagen probada

#### Scenario: El código de main no corresponde al candidato de staging
- **WHEN** el commit integrado no contiene el código de aplicación del candidato publicado en staging
- **THEN** el pipeline falla sin modificar el pin de producción

#### Scenario: Se autoriza la promoción de producción
- **WHEN** el usuario integra a `main` mediante PR el candidato validado en staging
- **THEN** ese merge autoriza al pipeline a actualizar automáticamente el pin productivo solo después de validar el candidato

#### Scenario: La validación del candidato falla
- **WHEN** falla CI, no está disponible la imagen validada o no se puede verificar la correspondencia del candidato
- **THEN** el pipeline no modifica el pin productivo y Flux conserva la versión actual

#### Scenario: El pipeline registra el pin productivo
- **WHEN** el pipeline termina correctamente la promoción automática
- **THEN** registra el pin de producción mediante un commit GitOps y ese commit no inicia otra promoción

#### Scenario: Se realiza la transición de pipelines
- **WHEN** se reemplaza el workflow anterior por el pipeline de staging
- **THEN** se desactiva el workflow anterior, terminan sus ejecuciones pendientes y solo después se activa la entrega nueva; la validación de PR permanece disponible mediante un workflow independiente

#### Scenario: La transición no puede verificar la desactivación
- **WHEN** no se puede confirmar que el workflow anterior está desactivado y sin ejecuciones capaces de actualizar staging
- **THEN** no se activa la entrega nueva ni se declara completada la transición
