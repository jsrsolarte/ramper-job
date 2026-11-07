# Spec Delta

## ADDED Requirements

### Requirement: Consultar vacantes por estado de seguimiento
El dashboard SHALL presentar como pestañas las recomendaciones pendientes de decisión y las vacantes aplicadas, en proceso, en entrevista, finalizadas y descartadas del perfil actual.

#### Scenario: La persona abre el dashboard de vacantes
- **WHEN** la persona consulta las recomendaciones sin elegir otro estado
- **THEN** el sistema muestra las vacantes pendientes de decisión

#### Scenario: La persona selecciona otra pestaña de seguimiento
- **WHEN** la persona selecciona aplicadas, en proceso, entrevista, finalizadas o descartadas
- **THEN** el sistema muestra solo las vacantes del perfil actual cuyo estado coincide con el filtro

#### Scenario: No hay vacantes en el estado elegido
- **WHEN** el perfil no tiene vacantes en el estado seleccionado
- **THEN** el sistema muestra un estado vacío para ese listado

#### Scenario: La persona descarta una vacante en seguimiento
- **WHEN** la persona descarta una vacante desde cualquier estado de seguimiento
- **THEN** deja de aparecer en el listado del estado anterior y aparece en el de descartadas

#### Scenario: La persona restaura una vacante descartada
- **WHEN** la persona restaura una vacante desde el listado de descartadas
- **THEN** deja de aparecer en descartadas y vuelve al listado del estado que tenía antes del descarte

### Requirement: Mostrar conteos por pestaña de seguimiento
Cada pestaña de seguimiento SHALL mostrar el número de vacantes únicas visibles para el perfil actual en ese estado.

#### Scenario: El estado contiene vacantes
- **WHEN** una pestaña de seguimiento contiene vacantes del perfil actual
- **THEN** el conteo coincide con las vacantes únicas presentadas en esa pestaña

#### Scenario: La persona cambia el estado de una vacante
- **WHEN** una vacante se mueve a otro estado de seguimiento
- **THEN** se actualizan los conteos de las pestañas de origen y destino junto con sus listados

#### Scenario: El estado no contiene vacantes
- **WHEN** el perfil actual no tiene vacantes en un estado
- **THEN** la pestaña de ese estado muestra el conteo cero

#### Scenario: Una vacante cambia de etapa
- **WHEN** una vacante se descarta, se restaura o se avanza a otra etapa
- **THEN** cada conteo refleja las vacantes únicas visibles en su estado actual

### Requirement: Ordenar las pestañas según el flujo de vacantes
El dashboard SHALL ordenar sus pestañas desde el análisis pendiente hasta las decisiones y avances de postulación.

#### Scenario: La persona consulta el dashboard de vacantes
- **WHEN** se muestran las pestañas del dashboard
- **THEN** aparecen en este orden: «Por analizar», «Recomendaciones», «Aplicadas», «En proceso», «Entrevista», «Finalizadas» y «Descartadas»
