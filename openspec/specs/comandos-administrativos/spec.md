# comandos-administrativos Specification

## Purpose
Proporciona a la persona administradora una interfaz segura para iniciar operaciones permitidas de la plataforma y consultar su estado sin ejecutar comandos arbitrarios.

## Requirements

### Requirement: Restringir el portal a administración
El portal de comandos SHALL estar disponible únicamente para la cuenta administrativa autorizada.

#### Scenario: La persona administradora abre el portal
- **WHEN** la cuenta administradora solicita el portal
- **THEN** el sistema presenta los comandos habilitados y sus estados recientes

#### Scenario: Una cuenta aspirante intenta ejecutar un comando
- **WHEN** una cuenta sin privilegios administrativos solicita el portal o su endpoint de ejecución
- **THEN** el sistema deniega el acceso y no inicia ningún trabajo

### Requirement: Exponer solo comandos permitidos
El portal SHALL permitir ejecutar únicamente operaciones definidas explícitamente por la aplicación.

#### Scenario: Se solicita una operación habilitada
- **WHEN** la persona administradora confirma un comando disponible
- **THEN** el sistema valida la solicitud y la acepta para ejecución

#### Scenario: Se intenta solicitar una operación arbitraria
- **WHEN** una solicitud incluye un comando o argumento no permitido
- **THEN** el sistema rechaza la solicitud sin ejecutarla

### Requirement: Ejecutar comandos de forma asíncrona
El portal SHALL encolar los comandos de larga duración y mostrar su estado sin mantener abierta la solicitud web hasta que terminen. SHALL considerar activo un comando solo mientras tenga trabajo en cola, una tarea ejecutándose o progreso reciente confirmado.

#### Scenario: Se inicia una actualización
- **WHEN** la persona administradora confirma una actualización manual
- **THEN** el sistema muestra que quedó en cola o en ejecución y permite consultar el resultado después

#### Scenario: Ya hay una ejecución equivalente en curso
- **WHEN** se solicita el mismo comando mientras una ejecución equivalente sigue activa
- **THEN** el sistema evita iniciar una ejecución concurrente duplicada y muestra la ejecución existente

#### Scenario: Una actualización manual queda interrumpida
- **WHEN** el comando permanece sin trabajo en cola, tarea activa ni progreso confirmado por más de 20 minutos
- **THEN** el sistema lo marca como fallido o parcial con un resumen seguro y permite iniciar una nueva actualización

#### Scenario: La actualización mantiene trabajo vigente
- **WHEN** el comando tiene unidades de trabajo pendientes o confirma progreso dentro de los últimos 20 minutos
- **THEN** el sistema lo conserva en ejecución y evita iniciar otro comando equivalente

### Requirement: Registrar la ejecución de comandos
El sistema SHALL conservar quién solicitó cada comando, cuándo empezó, su estado final y un resumen seguro del resultado.

#### Scenario: Una ejecución termina
- **WHEN** el comando termina correctamente o falla
- **THEN** el portal muestra su resultado y duración con errores saneados, sin secretos ni datos privados de perfiles
