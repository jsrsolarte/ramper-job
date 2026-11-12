# Spec Delta

## MODIFIED Requirements

### Requirement: Consultar métricas históricas de fuentes
El panel SHALL mostrar por fuente el volumen de ejecuciones, resultados, vacantes encontradas y duración durante un periodo seleccionable, y SHALL permitir consultar las ejecuciones individuales de búsqueda en orden cronológico. Durante una ejecución, SHALL mostrar progreso agregado por fuente a medida que se confirman unidades de trabajo, sin exponer datos de perfil.

#### Scenario: Hay historial de consultas de una fuente
- **WHEN** la persona administradora selecciona un periodo con ejecuciones registradas
- **THEN** el panel muestra conteos de ejecuciones exitosas y fallidas, vacantes encontradas y tiempo promedio de ejecución para cada fuente

#### Scenario: Una fuente presenta fallas
- **WHEN** se registra una consulta fallida o parcial durante el periodo
- **THEN** el panel muestra su frecuencia, el último éxito y un resumen seguro del error más reciente

#### Scenario: No hay historial para el periodo
- **WHEN** una fuente no tiene ejecuciones registradas en el periodo elegido
- **THEN** el panel indica que no hay datos para ese periodo y presenta desde cuándo existe instrumentación

#### Scenario: Consultar búsquedas individuales agrupadas por actualización
- **WHEN** la persona administradora abre el historial para un periodo con consultas de búsqueda registradas
- **THEN** el panel agrupa las búsquedas por lote de actualización y permite expandir cada grupo para consultar fecha, fuente, estado, cantidad de vacantes encontradas, duración y resumen seguro del error cuando exista

#### Scenario: Consultar más ejecuciones que las visibles en una página
- **WHEN** las ejecuciones del periodo exceden el tamaño de página
- **THEN** el panel permite recorrer las páginas restantes sin cambiar el periodo seleccionado

#### Scenario: Consultar un periodo sin ejecuciones
- **WHEN** no hay consultas de búsqueda registradas para el periodo seleccionado
- **THEN** el panel informa que no hubo ejecuciones en el intervalo

#### Scenario: Una actualización sigue procesándose por lotes
- **WHEN** quedan unidades de búsqueda activas o en cola para una fuente
- **THEN** el panel muestra su estado y los conteos agregados confirmados hasta el momento

#### Scenario: Consultar el estado real de una búsqueda por lotes
- **WHEN** una búsqueda tiene una unidad durable en cola, en ejecución o terminada
- **THEN** el historial muestra el estado de esa unidad y no presenta como ejecutándose una unidad que sigue en cola; las ejecuciones históricas terminales sin unidad durable conservan su estado registrado

### Requirement: Cerrar ejecuciones interrumpidas
La reconciliación periódica SHALL marcar como fallidas o parciales las ejecuciones de ingesta y sus comandos administrativos que permanezcan sin trabajo activo, en cola o con progreso confirmado por más de 20 minutos. SHALL usar una categoría segura de interrupción, conservar el historial y liberar los leases asociados.

#### Scenario: Un worker se detiene durante una ejecución
- **WHEN** una ejecución sigue marcada en curso por más de 20 minutos y no existe tarea o unidad de trabajo vigente para ella
- **THEN** la reconciliación registra su finalización y un resumen seguro de interrupción, actualiza el comando administrativo asociado y libera sus leases sin borrar el historial

#### Scenario: Una ejecución continúa avanzando
- **WHEN** existe trabajo activo o en cola, o una unidad confirmó progreso dentro de los últimos 20 minutos
- **THEN** la reconciliación conserva la ejecución en curso


#### Scenario: Una ejecución antigua no tiene unidad durable
- **WHEN** una ejecución sin unidad durable permanece registrada como activa durante más de 20 minutos
- **THEN** el historial la presenta como interrumpida y limita su duración visible a 20 minutos, siguiendo el umbral de reconciliación
