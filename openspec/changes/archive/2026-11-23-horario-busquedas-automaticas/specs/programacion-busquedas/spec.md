# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Consultar la próxima búsqueda automática
El sistema SHALL mostrar la fecha y hora local estimadas del siguiente ciclo automático global en el dashboard de aspirantes y en el centro administrativo, teniendo en cuenta la franja configurada.

#### Scenario: La persona aspirante consulta el dashboard
- **WHEN** el procesamiento está habilitado y existe una estimación válida
- **THEN** el dashboard muestra cuándo se espera la próxima búsqueda automática global

#### Scenario: La persona administradora consulta el centro
- **WHEN** la cuenta administradora abre el centro administrativo y existe una estimación válida
- **THEN** el centro muestra la misma fecha y hora estimadas que consulta una persona aspirante

#### Scenario: No existe una estimación confiable
- **WHEN** el sistema no cuenta con información suficiente para calcular la próxima ejecución automática
- **THEN** ambas vistas indican que el horario todavía no está disponible y no inventan una fecha

#### Scenario: El siguiente ciclo cae dentro de la franja
- **WHEN** el cálculo del siguiente ciclo cae en la franja de pausa
- **THEN** ambas vistas indican la pausa programada y estiman la búsqueda no antes del final de la franja

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
