# Spec Delta

## MODIFIED Requirements

### Requirement: Consultar métricas históricas de fuentes
El panel SHALL mostrar por fuente el volumen de ejecuciones, resultados, vacantes encontradas y duración durante un periodo seleccionable, y SHALL permitir consultar las ejecuciones individuales de búsqueda en orden cronológico.

#### Scenario: Hay historial de consultas de una fuente
- **WHEN** la persona administradora selecciona un periodo con ejecuciones registradas
- **THEN** el panel muestra conteos de ejecuciones exitosas y fallidas, vacantes encontradas y tiempo promedio de ejecución para cada fuente

#### Scenario: Una fuente presenta fallas
- **WHEN** se registra una consulta fallida o parcial durante el periodo
- **THEN** el panel muestra su frecuencia, el último éxito y un resumen seguro del error más reciente

#### Scenario: No hay historial para el periodo
- **WHEN** una fuente no tiene ejecuciones registradas en el periodo elegido
- **THEN** el panel indica que no hay datos para ese periodo y presenta desde cuándo existe instrumentación

#### Scenario: Consultar ejecuciones individuales
- **WHEN** la persona administradora abre el historial para un periodo con consultas de búsqueda registradas
- **THEN** el panel presenta cada consulta en orden de más reciente a más antigua, con fecha, fuente, estado, cantidad de vacantes encontradas, duración y resumen seguro del error cuando exista

#### Scenario: Consultar más ejecuciones que las visibles en una página
- **WHEN** las ejecuciones del periodo exceden el tamaño de página
- **THEN** el panel permite recorrer las páginas restantes sin cambiar el periodo seleccionado

#### Scenario: Consultar un periodo sin ejecuciones
- **WHEN** no hay consultas de búsqueda registradas para el periodo seleccionado
- **THEN** el panel informa que no hubo ejecuciones en el intervalo
