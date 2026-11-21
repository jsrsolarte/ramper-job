# Spec Delta

## MODIFIED Requirements

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
