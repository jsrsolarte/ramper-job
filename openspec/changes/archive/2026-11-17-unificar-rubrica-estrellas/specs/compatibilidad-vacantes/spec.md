## MODIFIED Requirements

### Requirement: Evaluación con una rúbrica fija y versionada
El sistema SHALL enviar al modelo una rúbrica común y versionada, y exigir una evaluación por criterio con puntaje de precisión definida en la rúbrica, estado de evidencia y soporte basado en el CV y la vacante.

#### Scenario: Se evalúa una vacante elegible
- **WHEN** el sistema solicita un análisis de compatibilidad
- **THEN** envía la misma versión vigente de la rúbrica para todos los perfiles y vacantes analizados con esa configuración

#### Scenario: Se evalúa una habilidad o experiencia requerida
- **WHEN** el modelo evalúa los criterios de la rúbrica
- **THEN** asigna precisión definida en la rúbrica dentro de los máximos de cada criterio: 2 para competencias y habilidades, 1 para experiencia, 1 para alineación, 0,5 para educación requerida y 0,5 para otros criterios explícitos, excluyendo ubicación y modalidad

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
El sistema SHALL calcular el puntaje final como la suma de los puntos por criterio menos las deducciones críticas configuradas, limitado al intervalo de 0 a 5, redondeado al medio punto más cercano, con empates hacia arriba.

#### Scenario: Suma válida
- **WHEN** el modelo devuelve puntajes válidos dentro de los límites de cada criterio
- **THEN** el puntaje guardado es la suma de los criterios menos las deducciones y se encuentra entre 0 y 5 en incrementos de 0,5

#### Scenario: Desglose inválido
- **WHEN** el modelo omite un criterio, devuelve puntos fuera de sus límites o un estado no admitido
- **THEN** el sistema rechaza el análisis como inválido y no guarda un puntaje parcial

#### Scenario: Puntaje o deducción inválidos
- **WHEN** un puntaje o deducción tiene una precisión no admitida o excede los límites versionados
- **THEN** el sistema rechaza el análisis y no guarda un puntaje parcial

### Requirement: Reanalizar resultados vigentes con una nueva rúbrica
El sistema SHALL convertir los análisis vigentes al introducir la escala de cinco estrellas sin solicitar un nuevo análisis, conservando los análisis anteriores para trazabilidad.

#### Scenario: Reprocesamiento de resultados existentes
- **WHEN** se activa el cambio a la nueva rúbrica
- **THEN** cada resultado existente se convierte sin reanálisis y conserva su versión, evidencia y trazabilidad original

#### Scenario: Reprocesamiento aún pendiente
- **WHEN** la conversión de una combinación todavía no termina
- **THEN** el sistema conserva el resultado previo y no lo presenta como si hubiera sido calculado con la nueva rúbrica

## ADDED Requirements

### Requirement: Convertir resultados históricos a la escala de estrellas
El sistema SHALL convertir cada resultado histórico de 0–10 dividiendo su valor entre dos y redondeando al medio punto más cercano, con empates hacia arriba, sin solicitar nuevos análisis ni perder trazabilidad.

#### Scenario: Convertir un resultado entre dos medias estrellas
- **WHEN** un resultado antiguo equivale a 3,25 estrellas
- **THEN** el resultado convertido es 3,5 estrellas y conserva su origen, desglose y evidencia

#### Scenario: Repetir o interrumpir la conversión
- **WHEN** la migración se reintenta o se interrumpe
- **THEN** cada resultado se convierte como máximo una vez y puede recuperarse sin mezclar escalas

#### Scenario: Activar la nueva escala
- **WHEN** se activa la nueva rúbrica
- **THEN** no se generan nuevos análisis de IA solo por la conversión y los resultados existentes siguen accesibles con su versión de origen
