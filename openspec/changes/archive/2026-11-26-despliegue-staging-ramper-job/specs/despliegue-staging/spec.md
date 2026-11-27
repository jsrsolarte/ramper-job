# Spec Delta

## Purpose

Permite empaquetar, desplegar y validar `ramper-job` en el entorno staging del servidor de forma trazable y aislada. El flujo mantiene separados los datos y credenciales de staging y producción.

## MODIFIED Requirements

### Requirement: Ejecutar la aplicación en procesos separados
La aplicación SHALL poder ejecutar el servidor web, el worker de tareas y el programador como procesos independientes desde la misma versión de la aplicación.

#### Scenario: Se inicia el servidor web
- **WHEN** el entorno ejecuta el proceso web con la configuración de staging
- **THEN** Django sirve la aplicación con `DEBUG` desactivado y escucha en el puerto configurado

#### Scenario: Se inician las tareas asíncronas
- **WHEN** el entorno ejecuta el worker y el programador
- **THEN** ambos usan la misma versión de aplicación y configuración de staging que el proceso web
### Requirement: Publicar imágenes trazables e inmutables
El sistema de entrega SHALL construir y publicar una imagen identificada por el commit de origen y SHALL NOT desplegar etiquetas mutables como `latest`.

#### Scenario: Se publica una versión candidata
- **WHEN** una revisión destinada a staging supera las validaciones de CI
- **THEN** el registro contiene una imagen identificable por su commit y el manifiesto de staging referencia esa imagen

#### Scenario: La validación de CI falla
- **WHEN** una validación obligatoria de CI falla
- **THEN** no se publica una versión candidata para desplegar en staging
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
### Requirement: Reconciliar staging mediante Flux
El entorno staging SHALL obtener la configuración de despliegue desde Git y SHALL ser aplicado por Flux en el namespace `staging`.

#### Scenario: Flux reconcilia una versión de staging
- **WHEN** se registra en Git una referencia aprobada a una imagen inmutable
- **THEN** Flux aplica el overlay de staging y el cambio queda asociado al commit y la imagen desplegados

#### Scenario: Se prepara el primer despliegue
- **WHEN** la aplicación todavía no está registrada en la raíz de Flux de staging
- **THEN** el personal administrador agrega una fuente y una reconciliación para el repositorio y overlay de `ramper-job` en staging

#### Scenario: Se prepara staging
- **WHEN** se crean o actualizan los recursos de esta capacidad
- **THEN** sus cambios se limitan al namespace y configuración de staging, sin alterar recursos, reconciliación ni referencias de imagen de producción
### Requirement: Aislar configuración y datos de staging
Staging SHALL usar credenciales, configuración, base de datos y archivos privados separados de producción; el sistema SHALL NOT copiar datos reales de producción a staging.

#### Scenario: Se configura una credencial
- **WHEN** staging necesita una clave de Django, base de datos, OmniRoute u otro servicio
- **THEN** el valor se proporciona desde un mecanismo de secretos fuera del repositorio y no aparece en imágenes, manifiestos versionados ni logs

#### Scenario: Se almacenan CV sintéticos en staging
- **WHEN** una cuenta carga un CV en staging
- **THEN** el archivo queda en almacenamiento privado y persistente, separado de producción, y se trata como descartable porque no hay copias de seguridad ni procedimiento de restauración

#### Scenario: Se prepara la base de datos de staging
- **WHEN** el despliegue necesita persistir perfiles, vacantes o estados de seguimiento
- **THEN** usa una base de datos independiente de producción, sin copias de seguridad ni procedimiento de restauración; sus datos se consideran descartables

#### Scenario: Se pierde un volumen de staging
- **WHEN** se pierde el nodo o un volumen persistente de staging
- **THEN** se acepta la pérdida de los datos almacenados y se recrea el entorno con datos sintéticos, sin restaurar desde un backup

#### Scenario: Se prepara una futura producción
- **WHEN** se configura un entorno de producción para Ramper Job mientras esta decisión siga vigente
- **THEN** no se aprovisionan copias de seguridad de PostgreSQL ni de los CV y todo dato se considera susceptible de pérdida

#### Scenario: Se revisa una publicación
- **WHEN** se publica o sirve un CV de staging
- **THEN** el archivo no queda accesible sin autorización de la aplicación
### Requirement: Provisionar la cuenta administradora inicial
El primer despliegue de staging SHALL permitir crear manualmente una sola cuenta administradora, fuera del registro público y sin exponer su contraseña.

#### Scenario: No existe una cuenta administradora
- **WHEN** el operador autorizado ejecuta el bootstrap inicial en staging e ingresa la contraseña en una terminal interactiva con entrada oculta
- **THEN** el sistema crea la cuenta administradora y permite iniciar sesión con ella

#### Scenario: Ya existe una cuenta administradora
- **WHEN** se vuelve a ejecutar el bootstrap después de crear la cuenta
- **THEN** el sistema rechaza crear otra cuenta y conserva la existente

#### Scenario: Se completa el bootstrap
- **WHEN** termina la creación de la cuenta
- **THEN** la contraseña no aparece en Git, manifiestos, argumentos, historial del shell ni logs
### Requirement: Verificar salud y reversión del despliegue
Una versión SHALL considerarse desplegada en staging solo después de que Flux la reconcilie y los procesos requeridos estén listos; debe existir una ruta de reversión a una imagen compatible anterior.

#### Scenario: Reconciliación y procesos listos
- **WHEN** Flux aplica la nueva versión
- **THEN** el proceso web, el worker y el programador quedan listos, y las comprobaciones de salud y disponibilidad responden correctamente

#### Scenario: Flujo principal disponible
- **WHEN** una cuenta de prueba accede a staging después del despliegue
- **THEN** puede iniciar sesión, abrir el dashboard y usar el flujo principal de la aplicación con datos de prueba

#### Scenario: Despliegue no saludable
- **WHEN** la nueva versión no supera las comprobaciones de disponibilidad o el flujo principal
- **THEN** la versión no se declara validada y puede revertirse mediante GitOps a la imagen inmutable anterior
### Requirement: Separar los pipelines de staging y producción
El sistema SHALL identificar por separado la validación de PR, la entrega a staging y el pipeline de producción activado por cambios integrados en `main`. La promoción a producción SHALL ocurrir automáticamente solo cuando el commit integrado contiene código de aplicación ya validado y publicado en staging.

#### Scenario: Se valida un cambio propuesto
- **WHEN** se abre o actualiza un PR de aplicación
- **THEN** CI ejecuta las validaciones correspondientes sin modificar el pin ni desplegar en ninguno de los entornos

#### Scenario: Se integra en main el código probado en staging
- **WHEN** se integra a `main` mediante PR un candidato ya validado en `staging`
- **THEN** el pipeline de producción valida el commit integrado y, si todas las verificaciones pasan, actualiza automáticamente el pin productivo al artefacto inmutable probado en staging

#### Scenario: El merge genera un SHA distinto
- **WHEN** el merge a `main` produce un SHA distinto al commit probado en `staging`
- **THEN** el pipeline verifica que el código de aplicación integrado corresponde al candidato aprobado y conserva el SHA y digest de la imagen probada

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
