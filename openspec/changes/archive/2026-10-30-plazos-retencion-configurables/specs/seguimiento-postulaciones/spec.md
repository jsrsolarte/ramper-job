# Spec Delta

## MODIFIED Requirements

### Requirement: Descartar recomendaciones inactivas
El sistema SHALL descartar por perfil las recomendaciones que permanezcan pendientes de decisión durante el plazo global de descarte configurado por la administración, cuyo valor inicial es de siete días, contado desde su entrada al estado Recomendaciones.

#### Scenario: Recomendación pendiente alcanza el plazo inicial
- **WHEN** no existe un valor administrativo guardado y una recomendación vigente lleva siete días o más pendiente de decisión
- **THEN** el sistema la cambia a descartada, conserva pendiente como estado previo y registra la fecha de entrada a descartadas

#### Scenario: Recomendación pendiente alcanza el plazo configurado
- **WHEN** existe un plazo administrativo vigente distinto y una recomendación pendiente alcanza ese plazo
- **THEN** la tarea periódica la descarta en su siguiente ejecución sin afectar seguimientos de otros perfiles

#### Scenario: El mismo plazo aplica a todos los perfiles
- **WHEN** la tarea evalúa recomendaciones pendientes de distintos perfiles
- **THEN** utiliza para todas el mismo plazo global configurado por la administración

#### Scenario: Recomendación aún no cumple el plazo
- **WHEN** una recomendación vigente lleva menos tiempo que el plazo de descarte configurado
- **THEN** el sistema la conserva en Recomendaciones

#### Scenario: La persona avanzó la vacante
- **WHEN** una vacante ya fue aplicada, descartada manualmente, finalizada o avanzó a otra etapa
- **THEN** la tarea automática no cambia su estado

#### Scenario: Dos perfiles tienen estados distintos
- **WHEN** una recomendación compartida cumple el plazo para un perfil pero otro perfil tiene un estado distinto
- **THEN** el sistema descarta únicamente el seguimiento del perfil vencido

#### Scenario: La persona restaura un descarte automático
- **WHEN** la persona restaura una recomendación descartada automáticamente
- **THEN** la vacante vuelve a Recomendaciones y el plazo de descarte comienza de nuevo desde esa restauración

#### Scenario: La tarea diaria se repite
- **WHEN** la tarea vuelve a procesar las mismas vacantes
- **THEN** no vuelve a cambiar estados ya descartados ni duplica acciones

### Requirement: Archivar estados de seguimiento sin actividad
El sistema SHALL archivar lógicamente por perfil los seguimientos cuyo estado no haya cambiado durante el plazo global de inactividad configurado por la administración, cuyo valor inicial es de 30 días.

#### Scenario: El seguimiento cumple el plazo inicial sin cambios
- **WHEN** no existe un valor administrativo guardado y un estado de seguimiento alcanza 30 días sin cambios
- **THEN** el sistema lo marca como archivado sin borrar físicamente el seguimiento, la vacante ni los datos de otros perfiles

#### Scenario: El seguimiento cumple el plazo de inactividad configurado
- **WHEN** existe un plazo administrativo vigente distinto y un seguimiento alcanza ese plazo sin cambiar de estado
- **THEN** la tarea periódica lo archiva en su siguiente ejecución

#### Scenario: El mismo plazo aplica a todos los perfiles
- **WHEN** la tarea evalúa seguimientos de distintos perfiles
- **THEN** utiliza para todos el mismo plazo global configurado por la administración

#### Scenario: Se archivan estados distintos
- **WHEN** una recomendación, una vacante aplicada, en proceso, en entrevista, finalizada o descartada cumple el plazo sin cambios
- **THEN** el sistema archiva el seguimiento correspondiente a ese perfil

#### Scenario: El estado cambia antes del plazo vigente
- **WHEN** una persona cambia el estado de seguimiento de una vacante
- **THEN** el cómputo de inactividad comienza de nuevo desde la fecha de entrada al estado actual

#### Scenario: La tarea diaria se ejecuta más de una vez
- **WHEN** la tarea de archivado vuelve a procesar un seguimiento ya archivado
- **THEN** el registro permanece archivado y la ejecución no duplica ni altera datos de la vacante
