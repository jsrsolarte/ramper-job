## MODIFIED Requirements

### Requirement: Probar ramas de trabajo en staging y separar la liberación
El sistema SHALL desplegar en staging únicamente código integrado en la rama `staging`, que SHALL seguir siendo la fuente de Flux. `main` SHALL reservarse para la liberación a producción; esta regla de ramas SHALL NOT habilitar por sí sola un despliegue de producción.

#### Scenario: Se solicita probar una rama de trabajo
- **WHEN** se integra una rama de trabajo en `staging`
- **THEN** el pipeline de staging valida el commit integrado y, solo si las validaciones pasan, publica su imagen inmutable y actualiza el pin del overlay en `staging`

#### Scenario: Flux aplica una rama seleccionada
- **WHEN** el pipeline actualiza el pin de imagen en `staging`
- **THEN** Flux reconcilia desde la rama `staging` y despliega la imagen del commit validado, sin cambiar la fuente de Flux a una rama de trabajo

#### Scenario: Se promueve código probado
- **WHEN** el usuario aprueba el resultado en staging
- **THEN** el código probado se integra a `main` mediante PR y no se promueve a producción automáticamente

#### Scenario: Dos pruebas de rama coinciden
- **WHEN** varios commits candidatos llegan a `staging` en rápida sucesión
- **THEN** las actualizaciones del pin se serializan y una ejecución antigua no reemplaza una candidata más reciente; cada imagen y resultado quedan identificables por SHA

## ADDED Requirements

### Requirement: Separar los pipelines de staging y producción
El sistema SHALL identificar por separado las validaciones, la entrega a staging y la preparación de liberaciones de producción, y SHALL conservar el mismo artefacto validado al preparar una promoción.

#### Scenario: Se valida un cambio propuesto
- **WHEN** se abre o actualiza un PR de aplicación
- **THEN** CI ejecuta las validaciones correspondientes sin modificar el pin ni desplegar en ninguno de los entornos

#### Scenario: Se integra un commit a main
- **WHEN** un cambio llega a `main`
- **THEN** el pipeline de producción valida y prepara la liberación sin modificar automáticamente el pin, los recursos ni la reconciliación de producción

#### Scenario: Se prepara una promoción productiva
- **WHEN** se prepara una versión aprobada en staging para producción
- **THEN** la versión identifica el SHA y el digest probados y reutiliza la imagen validada sin reconstruir silenciosamente otra imagen

#### Scenario: Se autoriza la promoción de producción
- **WHEN** se solicita modificar el pin o los recursos de producción
- **THEN** el cambio solo se realiza con autorización explícita para esa promoción y mediante el flujo GitOps aprobado

#### Scenario: La validación del candidato falla
- **WHEN** falla cualquier validación requerida del commit integrado en `staging`
- **THEN** el pipeline no cambia el pin de imagen de staging y conserva la versión previamente desplegada

#### Scenario: Se realiza la transición de pipelines
- **WHEN** se reemplaza el workflow anterior por el pipeline de staging
- **THEN** se desactiva el workflow anterior, terminan sus ejecuciones pendientes y solo después se activa la entrega nueva; la validación de PR permanece disponible mediante un workflow independiente

#### Scenario: La transición no puede verificar la desactivación
- **WHEN** no se puede confirmar que el workflow anterior está desactivado y sin ejecuciones capaces de actualizar staging
- **THEN** no se activa la entrega nueva ni se declara completada la transición
