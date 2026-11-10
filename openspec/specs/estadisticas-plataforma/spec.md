# Estadísticas de plataforma Specification

## Purpose

Da a la persona administradora una vista agregada del comportamiento de las vacantes y sus puntajes en toda la plataforma, complementaria a las métricas técnicas de operación y a la distribución individual de cada aspirante.

## Requirements

### Requirement: Restringir las estadísticas globales a administración
El sistema SHALL permitir consultar las estadísticas de plataforma únicamente a la cuenta administradora autorizada.

#### Scenario: La persona administradora consulta estadísticas
- **WHEN** la cuenta administradora autenticada abre las estadísticas globales
- **THEN** el sistema muestra las métricas agregadas disponibles

#### Scenario: Una cuenta aspirante solicita estadísticas globales
- **WHEN** una cuenta sin privilegios administrativos solicita la vista o sus datos
- **THEN** el sistema deniega el acceso sin revelar agregados administrativos

### Requirement: Consultar vacantes por estado de seguimiento
El panel SHALL mostrar conteos globales por estado personal de seguimiento, calculados sobre las relaciones entre perfil y vacante.

#### Scenario: Hay vacantes en distintos estados de seguimiento
- **WHEN** la persona administradora consulta los estados de seguimiento
- **THEN** el panel muestra conteos separados de pendiente de decisión, descartada, aplicada, en proceso, entrevista y finalizada, e indica la fecha del corte

#### Scenario: No hay registros en un estado
- **WHEN** ningún perfil tiene una vacante en uno de los estados de seguimiento
- **THEN** el panel muestra cero para ese estado sin omitirlo

### Requirement: Consultar la distribución global de puntuaciones
El panel SHALL mostrar la distribución agregada de los puntajes vigentes de compatibilidad, conservando su precisión decimal y señalando el tamaño y periodo de la muestra.

#### Scenario: Hay puntajes vigentes en el periodo
- **WHEN** la persona administradora selecciona un periodo con análisis vigentes
- **THEN** el panel muestra conteos por intervalos de puntaje, la mediana y el número de resultados considerados

#### Scenario: No hay puntajes vigentes en el periodo
- **WHEN** el periodo seleccionado no tiene puntajes válidos vigentes
- **THEN** el panel indica que aún no hay datos para esa consulta

#### Scenario: Existen análisis anteriores reemplazados
- **WHEN** una vacante y perfil tienen análisis previos que fueron reemplazados por un resultado vigente
- **THEN** la distribución cuenta solo el resultado vigente para esa combinación y evita duplicar su peso

#### Scenario: Hay puntajes de varias versiones de rúbrica
- **WHEN** existen resultados vigentes calculados con distintas versiones de rúbrica
- **THEN** el panel los presenta por versión y no combina sus puntajes en una sola distribución

### Requirement: Indicar periodo y cobertura de las puntuaciones
El panel SHALL permitir filtrar las estadísticas de puntuación por periodos definidos y señalar desde cuándo existe cobertura confiable.

#### Scenario: La persona cambia el periodo
- **WHEN** la persona administradora selecciona otro periodo disponible
- **THEN** los conteos y estadísticas de puntaje corresponden al intervalo seleccionado

#### Scenario: El periodo incluye fechas anteriores a la cobertura
- **WHEN** la consulta incluye fechas anteriores al inicio del historial disponible
- **THEN** el panel indica la fecha inicial de cobertura y no presenta datos faltantes como ceros

### Requirement: Consultar tiempos de búsqueda por fuente
El panel SHALL mostrar por fuente el volumen y la duración de consultas automáticas terminadas dentro del periodo seleccionado, junto con su proporción de resultados no exitosos.

#### Scenario: Hay consultas terminadas de varias fuentes
- **WHEN** la persona administradora elige un periodo con consultas automáticas terminadas
- **THEN** el panel muestra por fuente la cantidad, duración mediana, percentil 95 de duración y porcentaje no exitoso, calculados solo con ejecuciones `source_query` terminadas en ese periodo

#### Scenario: Se cambia el periodo
- **WHEN** la persona administradora selecciona otro periodo disponible
- **THEN** el resumen por fuente y las estadísticas de puntuación reflejan el mismo intervalo seleccionado

#### Scenario: No hay consultas terminadas
- **WHEN** el periodo seleccionado no contiene consultas automáticas terminadas
- **THEN** el panel informa que no hay datos de duración para ese intervalo

#### Scenario: Hay ejecuciones parciales o fallidas
- **WHEN** una consulta terminada tiene estado parcial, reintento o fallido
- **THEN** se incluye en el volumen y se cuenta como no exitosa en el porcentaje de su fuente

### Requirement: Mantener el resumen de búsquedas agregado
El resumen de rendimiento SHALL mostrar solo agregados por fuente y no exponer información de perfiles, vacantes o consultas individuales.

#### Scenario: Se muestra el rendimiento de una fuente
- **WHEN** la persona administradora consulta la tabla de rendimiento
- **THEN** el panel muestra únicamente la fuente y métricas agregadas, sin datos personales ni enlaces a ejecuciones individuales

### Requirement: Proteger información personal en estadísticas globales
El sistema SHALL mostrar estadísticas agregadas sin incluir perfiles identificables, CV, prompts ni contenido privado de vacantes.

#### Scenario: Se muestra una distribución o conteo
- **WHEN** el panel presenta estados o puntajes
- **THEN** muestra totales agregados sin enlaces a registros individuales ni atributos que identifiquen a una persona
