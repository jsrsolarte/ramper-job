# Spec Delta

## MODIFIED Requirements

### Requirement: Consultar la distribución global de puntuaciones
El panel SHALL mostrar la distribución agregada de los puntajes vigentes de compatibilidad en una escala visible de cero a cinco estrellas, conservando los puntajes originales para los cálculos y señalando el tamaño y periodo de la muestra.

#### Scenario: Hay puntajes vigentes en el periodo
- **WHEN** la persona administradora selecciona un periodo con análisis vigentes
- **THEN** el panel muestra conteos por intervalos de media estrella desde `0–<0,5` hasta `4,5–5`, la mediana convertida a estrellas y el número de resultados considerados

#### Scenario: La distribución convierte puntajes decimales
- **WHEN** los resultados considerados incluyen puntajes decimales en la escala interna de 0 a 10
- **THEN** el sistema convierte la mediana a estrellas dividiéndola entre dos, muestra hasta dos decimales y determina los intervalos usando los puntajes originales sin redondearlos individualmente

#### Scenario: No hay puntajes vigentes en el periodo
- **WHEN** el periodo seleccionado no tiene puntajes válidos vigentes
- **THEN** el panel indica que aún no hay datos para esa consulta

#### Scenario: Existen análisis anteriores reemplazados
- **WHEN** una vacante y perfil tienen análisis previos que fueron reemplazados por un resultado vigente
- **THEN** la distribución cuenta solo el resultado vigente para esa combinación y evita duplicar su peso

#### Scenario: Hay puntajes de varias versiones de rúbrica
- **WHEN** existen resultados vigentes calculados con distintas versiones de rúbrica
- **THEN** el panel los presenta por versión y no combina sus puntajes en una sola distribución

### Requirement: Preservar la coherencia de estadísticas tras la conversión
Las estadísticas SHALL usar la escala de estrellas y conservar el periodo, la muestra, la privacidad y la procedencia de la rúbrica.

#### Scenario: Se consultan resultados históricos convertidos
- **WHEN** el periodo incluye resultados convertidos y resultados nuevos
- **THEN** sus puntuaciones se muestran en la misma escala sin tratarlos como análisis nuevos ni duplicar resultados
