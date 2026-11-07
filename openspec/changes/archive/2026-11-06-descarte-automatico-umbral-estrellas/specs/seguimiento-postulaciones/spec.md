# Spec Delta

## ADDED Requirements

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
