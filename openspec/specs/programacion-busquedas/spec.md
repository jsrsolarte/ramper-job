# programacion-busquedas Specification

## Purpose

Permite consultar cuándo se espera el siguiente ciclo automático global de búsqueda de vacantes. La información sirve tanto a las personas aspirantes como a la administración y refleja el intervalo y el estado operativo vigentes.

## Requirements

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
### Requirement: Reflejar la pausa y el intervalo vigentes
El horario informado SHALL usar el intervalo automático vigente y SHALL indicar el estado pausado cuando la búsqueda automática no pueda comenzar.

#### Scenario: El procesamiento está pausado
- **WHEN** la persona consulta el horario mientras la pausa global está activa
- **THEN** ambas vistas indican que las búsquedas están pausadas y no presentan una fecha como si el ciclo fuera a ejecutarse

#### Scenario: Cambia el intervalo automático
- **WHEN** la administración modifica el intervalo de actualización de fuentes
- **THEN** la estimación refleja el intervalo vigente para el siguiente ciclo automático

#### Scenario: La franja programada está activa
- **WHEN** la persona consulta el horario durante la franja y la pausa global está desactivada
- **THEN** ambas vistas explican la pausa programada y muestran su hora de finalización

### Requirement: Distinguir el ciclo automático de otras búsquedas
El sistema SHALL identificar el horario como una estimación del ciclo automático global y SHALL explicar que otras acciones pueden iniciar búsquedas antes.

#### Scenario: Una búsqueda puede comenzar antes
- **WHEN** el dashboard o el centro administrativo muestra la próxima búsqueda automática
- **THEN** también aclara que una actualización manual o un cambio de perfil puede iniciar búsquedas antes de ese horario

#### Scenario: Se inicia una actualización manual
- **WHEN** la administración solicita una actualización manual
- **THEN** la hora de esa solicitud no se presenta como el horario del siguiente ciclo automático

### Requirement: Configurar una franja diaria de pausa automática
El centro administrativo SHALL permitir habilitar o deshabilitar una franja diaria de pausa y configurar su hora inicial y final en `America/Bogota`, con inicio inclusivo y fin exclusivo.

#### Scenario: No hay configuración previa
- **WHEN** aún no se ha guardado una configuración de franja
- **THEN** la pausa está habilitada desde las 21:00 hasta las 07:00 del día siguiente

#### Scenario: Se cambia la franja
- **WHEN** administración guarda horas inicial y final válidas y distintas
- **THEN** el sistema aplica la nueva franja de inmediato e indica la zona horaria

#### Scenario: Se configura una franja dentro del mismo día
- **WHEN** la hora inicial es anterior a la final
- **THEN** se pausa desde la inicial inclusive hasta la final exclusiva del mismo día

#### Scenario: Se introducen horas iguales o inválidas
- **WHEN** administración intenta guardar horas iguales o inválidas
- **THEN** el sistema rechaza el cambio y conserva la configuración previa

#### Scenario: Se deshabilita la franja
- **WHEN** administración deshabilita la pausa programada
- **THEN** la franja deja de restringir búsquedas automáticas sin alterar la pausa global ni la individual

### Requirement: Respetar la franja en búsquedas automáticas
El sistema SHALL impedir el inicio de nuevas consultas automáticas a fuentes durante la franja y conservar las unidades automáticas pendientes para reanudarlas tras su finalización.

#### Scenario: Llega un ciclo durante la pausa
- **WHEN** vence un ciclo automático dentro de la franja
- **THEN** no comienza una búsqueda ni se registra como ejecución iniciada y no se acumulan ciclos vencidos

#### Scenario: Una unidad automática está pendiente o se recupera
- **WHEN** hay unidades de búsqueda automáticas en cola o recuperables durante la franja
- **THEN** no comienzan nuevas consultas a fuentes y se conservan para reanudar

#### Scenario: Una consulta está en curso al comenzar la pausa
- **WHEN** empieza la franja mientras una consulta automática está en curso
- **THEN** puede completar su unidad actual y guardar el avance, pero no inicia otra consulta o unidad de obtención de detalles durante la franja

#### Scenario: Termina la franja
- **WHEN** llega el fin de la franja y la pausa global no está activa
- **THEN** se permite continuar el trabajo automático pendiente sin duplicados y se ejecuta como máximo un ciclo global debido, sin reproducir cada ciclo omitido

#### Scenario: Se cambia un perfil durante la pausa
- **WHEN** un cambio de perfil origina una búsqueda automática dentro de la franja
- **THEN** su búsqueda queda pendiente hasta que se permita iniciar, respetando la habilitación del perfil al reanudar

### Requirement: Mantener independientes los controles operativos
La franja SHALL limitar solamente las búsquedas automáticas y SHALL NOT modificar los controles de pausa global o individual.

#### Scenario: Administración solicita una búsqueda manual
- **WHEN** administración solicita una actualización manual durante la franja y la pausa global está desactivada
- **THEN** la búsqueda puede ejecutarse para perfiles habilitados

#### Scenario: La pausa global está activa
- **WHEN** la pausa global está activa durante o después de la franja
- **THEN** siguen aplicándose sus restricciones a búsquedas y análisis, incluso manuales

#### Scenario: Hay análisis de vacantes existentes
- **WHEN** solo está activa la franja de pausa automática
- **THEN** pueden continuar los análisis de vacantes ya obtenidas y el procesamiento de vacantes por URL manual

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
