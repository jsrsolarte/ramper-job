# Spec Delta

## Purpose

Recupera análisis de vacantes pendientes sin progreso, mantiene ejecuciones idempotentes y los reintenta hasta el vencimiento configurado para cada perfil.

## ADDED Requirements

### Requirement: Reconciliar análisis pendientes sin progreso
El sistema SHALL detectar periódicamente los análisis pendientes vigentes que no tengan un despacho o una ejecución activa reciente y SHALL volver a encolarlos.

#### Scenario: La tarea desapareció de la cola
- **WHEN** un análisis elegible permanece pendiente más allá del umbral de recuperación y no tiene una ejecución activa
- **THEN** el sistema lo vuelve a encolar y registra que fue recuperado

#### Scenario: El análisis dejó de ser vigente
- **WHEN** la revisión del perfil cambió, la vacante se desactivó o la ubicación ya no es elegible
- **THEN** el sistema no vuelve a encolar ese análisis

### Requirement: Evitar ejecuciones simultáneas duplicadas
El sistema SHALL permitir como máximo una ejecución activa por análisis, incluso si Celery entrega más de una vez una tarea o una tarea anterior reaparece después de una recuperación.

#### Scenario: Dos entregas compiten por el mismo análisis
- **WHEN** dos workers intentan iniciar el mismo análisis al mismo tiempo
- **THEN** solo uno obtiene el derecho de ejecutarlo y el otro termina sin llamar al modelo

#### Scenario: Se recibe una entrega repetida después de completar
- **WHEN** una tarea duplicada llega para un análisis ya completado o reemplazado
- **THEN** el worker termina sin volver a solicitar un análisis al modelo

### Requirement: Reintentar análisis hasta su vencimiento
El sistema SHALL reintentar con espera creciente limitada los análisis sin resultado hasta que transcurran los días de descarte configurados desde el primer hallazgo para ese perfil, conservando esa fecha entre revisiones. El sistema SHALL mostrar en la tarjeta el número de intentos fallidos.

#### Scenario: El servicio sigue fallando
- **WHEN** un análisis vigente falla y no ha vencido
- **THEN** el sistema lo conserva pendiente, muestra sus intentos y lo vuelve a encolar tras la espera

#### Scenario: El plazo vence
- **WHEN** transcurren los días configurados desde el primer hallazgo sin completar el análisis
- **THEN** el sistema deja de reintentarlo y lo descarta solo para ese perfil sin borrar la vacante compartida

#### Scenario: Un análisis se recupera con éxito
- **WHEN** un análisis recuperado se completa correctamente
- **THEN** el sistema cierra su ciclo de recuperación y no lo vuelve a encolar
