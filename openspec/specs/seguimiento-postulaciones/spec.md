# seguimiento-postulaciones Specification

## Purpose

Permite a cada persona organizar las oportunidades de su perfil según una secuencia de postulación y conservar el resultado final de cada proceso. El seguimiento se conserva aunque la vacante vuelva a analizarse con una revisión o configuración de IA nueva.

## Requirements

### Requirement: Registrar un estado personal por vacante
El sistema SHALL conservar por separado para cada perfil y vacante un estado de seguimiento, independiente del estado y las versiones del análisis de IA.

#### Scenario: Se crea seguimiento para una vacante recomendada
- **WHEN** una vacante aparece como recomendación de un perfil y aún no tiene seguimiento
- **THEN** el sistema la considera pendiente de decisión para ese perfil

#### Scenario: Dos perfiles siguen la misma publicación
- **WHEN** dos perfiles tienen análisis de la misma vacante
- **THEN** cada perfil puede mantener un estado de seguimiento distinto

#### Scenario: Se reprocesa el análisis
- **WHEN** se crea un análisis nuevo para la misma vacante y perfil
- **THEN** el estado de seguimiento existente se conserva

### Requirement: Cambiar el estado de seguimiento de una vacante
El sistema SHALL permitir avanzar una vacante únicamente por estas etapas: pendiente de decisión, aplicada, en proceso y entrevista. Desde aplicada, en proceso o entrevista, la persona también puede marcar el proceso como finalizado. El sistema SHALL rechazar cualquier transición que salte o retroceda etapas.

#### Scenario: La persona inicia una postulación
- **WHEN** la persona cambia una vacante pendiente de decisión a aplicada
- **THEN** el sistema guarda ese estado para su perfil y muestra la vacante en aplicadas

#### Scenario: La postulación avanza de forma secuencial
- **WHEN** la persona cambia una vacante aplicada a en proceso o una vacante en proceso a entrevista
- **THEN** el sistema guarda la etapa siguiente y muestra la vacante en el listado correspondiente

#### Scenario: El proceso termina sin continuar
- **WHEN** la persona marca como finalizado un proceso en estado aplicada, en proceso o entrevista
- **THEN** el sistema guarda la vacante como finalizada y la muestra en ese listado

#### Scenario: Se intenta saltar o retroceder una etapa
- **WHEN** la persona intenta mover una vacante a una etapa que no es la siguiente permitida
- **THEN** el sistema rechaza el cambio y conserva el estado de seguimiento vigente

#### Scenario: El seguimiento no cambia el análisis de IA
- **WHEN** la persona avanza una vacante por el flujo de postulación
- **THEN** el sistema conserva sin cambios el estado técnico y el resultado del análisis de IA

### Requirement: Descartar una vacante desde cualquier estado
El sistema SHALL permitir que la persona descarte una vacante desde cualquier estado, incluido finalizada, y conservar el estado que tenía inmediatamente antes del descarte.

#### Scenario: La persona descarta una vacante en cualquier etapa
- **WHEN** la persona descarta una vacante pendiente, aplicada, en proceso, en entrevista o finalizada
- **THEN** el sistema la muestra como descartada y conserva la etapa previa para poder restaurarla

### Requirement: Restaurar una vacante descartada
El sistema SHALL permitir restaurar una vacante descartada al estado que tenía inmediatamente antes de descartarse.

#### Scenario: La persona restaura una vacante descartada
- **WHEN** la persona restaura una vacante descartada
- **THEN** el sistema recupera su estado previo al descarte y vuelve a incluirla en el listado correspondiente

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

### Requirement: Descartar recomendaciones inactivas
El sistema SHALL descartar por perfil las recomendaciones que permanezcan pendientes de decisión durante el plazo global de descarte configurado por la administración, cuyo valor inicial es de siete días, contado desde su entrada al estado Recomendaciones.

#### Scenario: Recomendación pendiente alcanza el plazo inicial
- **WHEN** no existe un valor administrativo guardado y una recomendación vigente lleva siete días o más pendiente de decisión
- **THEN** el sistema la cambia a descartada, conserva pendiente como estado previo y registra la fecha de entrada a descartadas

#### Scenario: Recomendación pendiente alcanza el plazo configurado
- **WHEN** existe un plazo administrativo vigente distinto y una recomendación pendiente alcanza ese plazo
- **THEN** la tarea periódica la descarta en su siguiente ejecución sin afectar seguimientos de otros perfiles

#### Scenario: Recomendación aún no cumple el plazo
- **WHEN** una recomendación vigente lleva menos tiempo que el plazo de descarte configurado
- **THEN** el sistema la conserva en Recomendaciones

#### Scenario: La persona avanzó la vacante
- **WHEN** una vacante ya fue aplicada, descartada manualmente, finalizada o avanzó a otra etapa
- **THEN** la tarea automática no cambia su estado

#### Scenario: Dos perfiles tienen estados distintos
- **WHEN** una recomendación compartida cumple el plazo configurado para un perfil pero otro perfil tiene un estado distinto
- **THEN** el sistema descarta únicamente el seguimiento del perfil vencido

#### Scenario: La persona restaura un descarte automático
- **WHEN** la persona restaura una recomendación descartada automáticamente
- **THEN** la vacante vuelve a Recomendaciones y el plazo de descarte comienza de nuevo desde esa restauración

#### Scenario: La tarea diaria se repite
- **WHEN** la tarea vuelve a procesar las mismas vacantes
- **THEN** no vuelve a cambiar estados ya descartados ni duplica acciones

### Requirement: Descartar automáticamente por debajo del umbral de descubrimiento
El sistema SHALL enviar a Descartadas una vacante recién descubierta cuyo análisis completo obtenga un puntaje menor que el umbral del perfil guardado al descubrirla.

#### Scenario: El análisis queda por debajo del umbral
- **WHEN** termina el análisis completo de una vacante cuyo puntaje es menor que el umbral guardado para ese descubrimiento
- **THEN** el sistema la registra en Descartadas como descarte automático

#### Scenario: El análisis alcanza el umbral
- **WHEN** termina el análisis completo de una vacante cuyo puntaje es igual o superior al umbral guardado para ese descubrimiento
- **THEN** el sistema la conserva en Recomendaciones, pendiente de decisión

#### Scenario: Umbral de cero
- **WHEN** termina el análisis de una vacante descubierta con umbral cero
- **THEN** el sistema no la descarta automáticamente por puntaje

### Requirement: Conservar el umbral aplicado a cada descubrimiento
El sistema SHALL evaluar cada vacante usando el umbral capturado cuando se descubrió por primera vez para el perfil, sin volver a aplicar cambios posteriores del perfil a esa vacante.

#### Scenario: El umbral cambia antes de completar el análisis
- **WHEN** cambia el umbral del perfil después del descubrimiento pero antes de terminar el análisis
- **THEN** el sistema evalúa la vacante con el valor guardado al descubrirla

#### Scenario: Se reanaliza una vacante existente
- **WHEN** se completa un análisis posterior de una vacante que ya fue evaluada con el umbral de descubrimiento
- **THEN** el sistema no cambia su estado por el umbral vigente en ese momento

### Requirement: Preservar decisiones y estados de seguimiento
El descarte automático SHALL crear un estado Descartadas para vacantes nuevas y SHALL NOT reemplazar una decisión o etapa de seguimiento existente.

#### Scenario: La vacante ya tiene una etapa de seguimiento
- **WHEN** termina un análisis de una vacante que ya fue movida a Aplicadas, En proceso, Entrevista o Finalizadas
- **THEN** el sistema conserva esa etapa sin descartarla automáticamente

#### Scenario: La vacante ya fue descartada por la persona
- **WHEN** termina o se repite el análisis de una vacante ya descartada
- **THEN** el sistema conserva el estado descartado y no la reactiva

#### Scenario: Vacante descubierta antes de habilitar la regla
- **WHEN** se analiza una vacante que ya existía antes de habilitar el descarte por puntaje
- **THEN** el sistema conserva su seguimiento y no le aplica retroactivamente el umbral
