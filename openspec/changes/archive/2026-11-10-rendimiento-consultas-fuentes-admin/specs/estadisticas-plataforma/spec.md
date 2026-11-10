# Spec Delta

## ADDED Requirements

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
