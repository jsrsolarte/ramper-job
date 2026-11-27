# Spec Delta

## MODIFIED Requirements

### Requirement: Reconciliar análisis pendientes sin progreso
El sistema SHALL detectar periódicamente los análisis pendientes vigentes que no tengan un despacho o una ejecución activa reciente y SHALL volver a encolarlos.

#### Scenario: La tarea desapareció de la cola
- **WHEN** un análisis elegible permanece pendiente más allá del umbral de recuperación y no tiene una ejecución activa
- **THEN** el sistema lo vuelve a encolar y registra que fue recuperado

#### Scenario: El perfil cambia antes de completar
- **WHEN** la revisión del perfil cambia mientras no existe un resultado completado
- **THEN** el sistema recupera el trabajo con la revisión vigente sin duplicar ejecuciones

#### Scenario: El análisis dejó de ser vigente
- **WHEN** la vacante se desactivó o la ubicación ya no es elegible
- **THEN** el sistema no vuelve a encolar ese análisis
