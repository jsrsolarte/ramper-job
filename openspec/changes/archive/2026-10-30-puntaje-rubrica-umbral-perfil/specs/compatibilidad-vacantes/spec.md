# Spec Delta

## MODIFIED Requirements

### Requirement: Resultado explicable de compatibilidad
El sistema SHALL conservar para cada análisis un puntaje entero de 0 a 10, el desglose de criterios de la rúbrica, la evidencia que respalda cada criterio, razones de coincidencia y requisitos no coincidentes o no evidenciados en el CV.

#### Scenario: Análisis completo
- **WHEN** el modelo devuelve un desglose válido para todos los criterios
- **THEN** el resultado incluye el puntaje entero de 0 a 10 calculado por el sistema, los criterios evaluados, su evidencia, razones de coincidencia y requisitos no coincidentes o no evidenciados

## ADDED Requirements

### Requirement: Evaluación con una rúbrica fija y versionada
El sistema SHALL enviar al modelo una rúbrica común y versionada, y exigir una evaluación por criterio con puntaje entero, estado de evidencia y soporte basado en el CV y la vacante.

#### Scenario: Se evalúa una vacante elegible
- **WHEN** el sistema solicita un análisis de compatibilidad
- **THEN** envía la misma versión vigente de la rúbrica para todos los perfiles y vacantes analizados con esa configuración

#### Scenario: Se evalúa una habilidad o experiencia requerida
- **WHEN** el modelo evalúa los criterios de la rúbrica
- **THEN** asigna de 0 a 4 puntos a competencias y habilidades requeridas, de 0 a 2 a experiencia y responsabilidades relevantes, de 0 a 2 a alineación del cargo o sector, de 0 a 1 a educación o certificaciones explícitamente requeridas y de 0 a 1 a otros criterios explícitos del perfil, excluyendo ubicación

#### Scenario: Criterio no requerido o no aplicable
- **WHEN** la vacante no establece un requisito educativo ni existe otro criterio explícito del perfil que corresponda evaluar
- **THEN** el criterio aplicable recibe su máximo de puntos y queda marcado como `no_aplica`

#### Scenario: Falta evidencia en el CV
- **WHEN** el CV no aporta evidencia suficiente para un criterio aplicable
- **THEN** el criterio recibe cero puntos, queda marcado como `sin_evidencia` y el sistema distingue esa ausencia de una contradicción explícita

#### Scenario: Evidencia contradice un requisito
- **WHEN** la evidencia disponible contradice un criterio aplicable
- **THEN** el criterio recibe cero puntos y queda marcado como `contradicho` con evidencia que sustente la contradicción

#### Scenario: Ubicación ya validada
- **WHEN** el sistema calcula compatibilidad para una vacante que superó la elegibilidad de ubicación o modalidad
- **THEN** no añade ni resta puntos por ubicación o modalidad en la rúbrica

### Requirement: Puntaje final calculado por el sistema
El sistema SHALL calcular el puntaje final como la suma de los puntos enteros otorgados por los criterios de la rúbrica, cuyo máximo conjunto es 10.

#### Scenario: Suma válida
- **WHEN** el modelo devuelve puntajes válidos dentro de los límites de cada criterio
- **THEN** el puntaje guardado es la suma exacta de esos puntajes y se encuentra entre 0 y 10

#### Scenario: Desglose inválido
- **WHEN** el modelo omite un criterio, devuelve puntos fuera de sus límites o un estado no admitido
- **THEN** el sistema rechaza el análisis como inválido y no guarda un puntaje parcial

### Requirement: Conservar la versión de rúbrica aplicada
El sistema SHALL conservar en cada análisis la versión de configuración y rúbrica, además del desglose de criterios y su evidencia, para permitir interpretar y comparar resultados.

#### Scenario: Análisis guardado
- **WHEN** un análisis se completa correctamente
- **THEN** queda asociada la versión exacta de la rúbrica utilizada junto a sus criterios, puntajes, estados y evidencia

### Requirement: Reanalizar resultados vigentes con una nueva rúbrica
El sistema SHALL reprocesar en segundo plano los análisis vigentes cuando se introduzca la nueva escala y rúbrica, conservando los análisis anteriores para trazabilidad.

#### Scenario: Reprocesamiento de resultados existentes
- **WHEN** se activa el cambio a la nueva rúbrica
- **THEN** cada combinación vigente de perfil y vacante con análisis completo se programa para un nuevo análisis y el análisis previo permanece consultable

#### Scenario: Reprocesamiento aún pendiente
- **WHEN** el nuevo análisis de una combinación todavía no termina
- **THEN** el sistema conserva el resultado previo y no lo presenta como si hubiera sido calculado con la nueva rúbrica
