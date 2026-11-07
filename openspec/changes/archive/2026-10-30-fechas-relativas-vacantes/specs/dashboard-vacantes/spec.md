# Spec Delta

## ADDED Requirements

### Requirement: Mostrar antigüedad de publicación
El dashboard SHALL mostrar cuánto tiempo ha pasado desde la publicación de una vacante cuando la fuente proporciona esa fecha.

#### Scenario: La vacante tiene fecha de publicación
- **WHEN** una vacante visible tiene una fecha de publicación
- **THEN** el dashboard muestra una etiqueta relativa en español, como «Publicada hace 30 min» o «Publicada hace 2 horas»

#### Scenario: La vacante no tiene fecha de publicación
- **WHEN** una vacante visible no tiene fecha de publicación disponible
- **THEN** el dashboard omite la etiqueta de antigüedad sin inventar una fecha

### Requirement: Mostrar antigüedad del análisis
El dashboard SHALL mostrar cuánto tiempo ha pasado desde que se completó el análisis vigente de la vacante para el perfil actual.

#### Scenario: Vacante recomendada con análisis completado
- **WHEN** una vacante aparece en Recomendaciones con un análisis vigente completado
- **THEN** el dashboard muestra «Analizada hace…» usando la fecha de finalización de ese análisis para el perfil actual

#### Scenario: Vacante todavía sin análisis completado
- **WHEN** una vacante aún no tiene un análisis vigente completado para el perfil actual
- **THEN** el dashboard no muestra una etiqueta de análisis como si ya se hubiera completado

### Requirement: Mostrar antigüedad del estado actual
El dashboard SHALL mostrar cuánto tiempo lleva una vacante en el estado de seguimiento actual del perfil.

#### Scenario: Vacante en una etapa de postulación
- **WHEN** una vacante se muestra como aplicada, en proceso, en entrevista, finalizada o descartada
- **THEN** el dashboard muestra una etiqueta como «Aplicada hace…» o «Entrevista hace…» basada en la fecha en que entró a ese estado

#### Scenario: Vacante en Recomendaciones
- **WHEN** una vacante aparece en Recomendaciones sin haber avanzado a otro estado
- **THEN** el dashboard usa la fecha de finalización del análisis vigente para indicar «Analizada hace…»

#### Scenario: La vacante cambia de estado
- **WHEN** una vacante pasa a un estado distinto
- **THEN** la antigüedad del nuevo estado comienza desde ese cambio y no reutiliza la duración del estado anterior

#### Scenario: Mostrar tiempos relativos
- **WHEN** el dashboard muestra una fecha de publicación, análisis o estado
- **THEN** expresa el tiempo transcurrido con unidades legibles en español y conserva la fecha y hora exactas en un formato accesible
