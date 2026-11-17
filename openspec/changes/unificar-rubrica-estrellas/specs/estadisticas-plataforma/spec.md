## MODIFIED Requirements

### Requirement: Consultar la distribución global de puntuaciones
El panel SHALL mostrar la distribución agregada de los puntajes vigentes de compatibilidad, usando estrellas visuales para puntuaciones y medianas de cero a cinco en incrementos de 0,5, con etiquetas accesibles para su valor exacto, y señalando el tamaño y periodo de la muestra.

#### Scenario: Hay puntajes vigentes en el periodo
- **WHEN** la persona administradora selecciona un periodo con análisis vigentes
- **THEN** el panel muestra conteos por puntuaciones de estrellas, la mediana y el número de resultados considerados

#### Scenario: No hay puntajes vigentes en el periodo
- **WHEN** el periodo seleccionado no tiene puntajes válidos vigentes
- **THEN** el panel indica que aún no hay datos para esa consulta

#### Scenario: Existen análisis anteriores reemplazados
- **WHEN** una vacante y perfil tienen análisis previos que fueron reemplazados por un resultado vigente
- **THEN** la distribución cuenta solo el resultado vigente para esa combinación y evita duplicar su peso

#### Scenario: Hay puntajes de varias versiones de rúbrica
- **WHEN** existen resultados vigentes calculados con distintas versiones de rúbrica
- **THEN** el panel los presenta por versión y mantiene su origen identificable y no confunde escalas ni versiones

## ADDED Requirements

### Requirement: Preservar la coherencia de estadísticas tras la conversión
Las estadísticas SHALL usar la escala de estrellas y conservar el periodo, la muestra, la privacidad y la procedencia de la rúbrica.

#### Scenario: Se consultan resultados históricos convertidos
- **WHEN** el periodo incluye resultados convertidos y resultados nuevos
- **THEN** sus puntuaciones se muestran en la misma escala sin tratarlos como análisis nuevos ni duplicar resultados
