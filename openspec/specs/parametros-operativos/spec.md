# parametros-operativos Specification

## Purpose

Permite a la persona administradora ajustar valores operativos aprobados desde el centro administrativo y conocer cuándo entran en vigor los cambios.

## Requirements

### Requirement: Consultar y modificar parámetros operativos permitidos
El sistema SHALL permitir a la persona administradora modificar solo los parámetros operativos que la plataforma expone explícitamente.

#### Scenario: La persona administradora consulta los parámetros
- **WHEN** la cuenta administradora abre la configuración operativa
- **THEN** el sistema muestra los parámetros habilitados y sus valores vigentes

#### Scenario: Se cambia un parámetro permitido
- **WHEN** la persona administradora guarda un nuevo valor válido para un parámetro habilitado
- **THEN** el sistema persiste el valor y aplica el cambio según su comportamiento definido

#### Scenario: Se intenta cambiar una clave no permitida
- **WHEN** una solicitud incluye una clave de configuración que la interfaz no habilita
- **THEN** el sistema rechaza la modificación y conserva la configuración vigente

### Requirement: Administrar el intervalo de actualización de fuentes
El sistema SHALL permitir a la persona administradora configurar en minutos el intervalo automático de actualización de fuentes, cuyo valor inicial es 120 minutos.

#### Scenario: No existe un valor guardado
- **WHEN** todavía no se guardó un intervalo desde el panel
- **THEN** el sistema usa el valor inicial de 120 minutos, salvo que el ambiente haya definido otro valor inicial

#### Scenario: Se guarda un intervalo válido
- **WHEN** la persona administradora guarda un intervalo válido en minutos
- **THEN** el sistema programa los siguientes ciclos automáticos con el intervalo nuevo sin iniciar una actualización inmediata

#### Scenario: Se guarda un intervalo inválido
- **WHEN** el valor no es un número entero positivo dentro de los límites operativos permitidos
- **THEN** el sistema rechaza el cambio, explica el error y conserva el intervalo vigente

### Requirement: Auditar cambios de parámetros operativos
El sistema SHALL registrar quién modificó cada parámetro operativo, cuándo se cambió y cuál fue el valor anterior y nuevo.

#### Scenario: Se aplica un cambio de intervalo
- **WHEN** se guarda correctamente un nuevo intervalo de actualización
- **THEN** el historial conserva actor, fecha, valor anterior y valor nuevo sin incluir secretos

#### Scenario: Una cuenta sin permiso intenta cambiar un parámetro
- **WHEN** una cuenta no administrativa envía una solicitud de modificación
- **THEN** el sistema deniega el cambio y no revela ni modifica la configuración

### Requirement: Configurar plazos de retención de vacantes
El sistema SHALL permitir a la persona administradora configurar globalmente para toda la plataforma, en días, el plazo para descartar recomendaciones pendientes y el plazo para archivar seguimientos inactivos, con valores iniciales de 7 y 30 días respectivamente.

#### Scenario: No existen valores configurados
- **WHEN** todavía no se guardaron plazos desde el panel
- **THEN** el sistema muestra y aplica 7 días para el descarte automático y 30 días para el archivado de seguimientos

#### Scenario: Se modifica un plazo
- **WHEN** la persona administradora guarda un nuevo plazo entero válido entre 1 y 365 días
- **THEN** el sistema guarda y audita el cambio, y el proceso correspondiente lo aplica desde su siguiente ejecución diaria sin iniciar una ejecución inmediata

#### Scenario: Se intenta guardar un plazo inválido
- **WHEN** el valor no es un entero entre 1 y 365 días
- **THEN** el sistema rechaza el cambio, explica el error y conserva el plazo vigente

#### Scenario: Se consulta la configuración
- **WHEN** la persona administradora abre los parámetros operativos
- **THEN** puede distinguir el plazo de descarte de recomendaciones del plazo de archivado por inactividad

#### Scenario: Los valores son globales
- **WHEN** la persona administradora cambia cualquiera de los dos plazos
- **THEN** el nuevo valor se aplica por igual a las tareas que procesan todos los perfiles y no existe una configuración individual por perfil
