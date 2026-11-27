# Spec Delta

## MODIFIED Requirements

### Requirement: Consultar la próxima búsqueda automática
El sistema SHALL mostrar la fecha y hora local estimadas del siguiente ciclo automático global en el dashboard de aspirantes y en el centro administrativo, teniendo en cuenta la franja configurada y diferenciando un ciclo vencido de uno futuro.

#### Scenario: La persona aspirante consulta el dashboard
- **WHEN** el procesamiento está habilitado y existe una estimación futura válida
- **THEN** el dashboard muestra cuándo se espera la próxima búsqueda automática global

#### Scenario: La persona administradora consulta el centro
- **WHEN** la cuenta administradora abre el centro administrativo y existe una estimación válida
- **THEN** el centro muestra el mismo estado y fecha estimada que consulta una persona aspirante

#### Scenario: No existe una estimación confiable
- **WHEN** el sistema no cuenta con información suficiente para calcular la próxima ejecución automática
- **THEN** ambas vistas indican que el horario todavía no está disponible y no inventan una fecha

#### Scenario: El siguiente ciclo cae dentro de la franja
- **WHEN** el cálculo del siguiente ciclo cae en la franja de pausa
- **THEN** ambas vistas indican la pausa programada y estiman la búsqueda no antes del final de la franja

#### Scenario: Un ciclo está vencido
- **WHEN** la hora estimada ya llegó o pasó y no se ha registrado el inicio del ciclo correspondiente, fuera de la pausa programada y global
- **THEN** ambas vistas indican que la búsqueda está retrasada o pendiente y muestran la hora vencida solo como hora estimada anterior, sin llamarla próxima hora ni afirmar que ya se ejecutó

#### Scenario: La página permanece abierta
- **WHEN** una pantalla con una estimación futura permanece abierta hasta que esa hora pasa
- **THEN** deja de presentarla como próxima fecha y actualiza el estado consultando información vigente o indica que debe actualizarse

#### Scenario: El ciclo retrasado comienza
- **WHEN** se registra el inicio real del ciclo pendiente
- **THEN** las vistas dejan de mostrar ese ciclo como retrasado y presentan el estado o estimación resultante del ciclo siguiente

#### Scenario: Se consulta una estimación retrasada
- **WHEN** una persona abre o actualiza el dashboard o el centro administrativo
- **THEN** la consulta no inicia búsquedas, no modifica su programación y no inventa una hora futura

## ADDED Requirements

### Requirement: Mostrar una búsqueda en curso
El dashboard y el centro administrativo SHALL indicar cuando exista trabajo de búsqueda en curso confirmado y mostrar por separado la próxima estimación automática cuando sea fiable.

#### Scenario: Hay trabajo activo y una próxima estimación
- **WHEN** existe una búsqueda con trabajo activo confirmado y una estimación futura fiable del siguiente ciclo automático global
- **THEN** ambas vistas muestran que hay una búsqueda en curso y la próxima hora estimada como información separada

#### Scenario: No hay estimación fiable
- **WHEN** hay una búsqueda en curso pero no existe una próxima hora fiable
- **THEN** ambas vistas muestran la búsqueda en curso y explican que la próxima hora no está disponible

#### Scenario: El trabajo solo está en cola o pausado
- **WHEN** el trabajo está en cola o diferido y no existe actividad confirmada
- **THEN** las vistas indican que está pendiente o pausado y no lo presentan como búsqueda en curso

#### Scenario: Un trabajo parece interrumpido
- **WHEN** solo existen registros antiguos sin actividad confirmada o con concesiones vencidas
- **THEN** las vistas indican que su estado es incierto o pendiente de recuperación y no afirman que siga en curso

#### Scenario: Coinciden una búsqueda y una pausa
- **WHEN** una unidad sigue en curso y la pausa global o programada impide iniciar más trabajo
- **THEN** las vistas indican la actividad confirmada y la pausa separadamente sin prometer un nuevo inicio

### Requirement: Facilitar la revisión administrativa de un retraso
El centro administrativo SHALL mostrar la hora estimada vencida y la hora del último inicio registrado cuando estén disponibles, sin atribuir una causa no comprobada.

#### Scenario: Existe un ciclo vencido
- **WHEN** administración consulta un ciclo automático vencido
- **THEN** puede distinguir la hora vencida y el último inicio registrado o su ausencia, y sabe que el inicio siguiente todavía no está confirmado
