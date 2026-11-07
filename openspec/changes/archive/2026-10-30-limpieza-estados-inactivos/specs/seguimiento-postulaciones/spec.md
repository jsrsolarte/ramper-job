# Spec Delta

## ADDED Requirements

### Requirement: Archivar estados de seguimiento sin actividad
El sistema SHALL archivar lógicamente por perfil los seguimientos cuyo estado no haya cambiado durante 30 días.

#### Scenario: El seguimiento cumple 30 días sin cambios
- **WHEN** un estado de una vacante para un perfil alcanza 30 días sin cambiar
- **THEN** el sistema lo marca como archivado sin borrar físicamente el seguimiento, la vacante ni los datos de otros perfiles

#### Scenario: El estado cambia antes del plazo
- **WHEN** una persona cambia el estado de seguimiento de una vacante
- **THEN** el plazo de 30 días comienza de nuevo desde la fecha de entrada al estado actual

#### Scenario: Se archivan estados distintos
- **WHEN** una recomendación, una vacante aplicada, en proceso, en entrevista, finalizada o descartada cumple el plazo sin cambios
- **THEN** el sistema archiva el seguimiento correspondiente a ese perfil

#### Scenario: La tarea diaria se ejecuta más de una vez
- **WHEN** la tarea de archivado vuelve a procesar un seguimiento ya archivado
- **THEN** el registro permanece archivado y la ejecución no duplica ni altera datos de la vacante
