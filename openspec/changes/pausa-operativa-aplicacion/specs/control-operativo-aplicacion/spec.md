# Spec Delta

## Purpose

Permite a la administración detener y reanudar de forma global la búsqueda y el análisis de vacantes. El centro administrativo permanece disponible para controlar esta pausa.

## ADDED Requirements

### Requirement: Administrar la pausa global de procesamiento de vacantes
El sistema SHALL permitir a la persona administradora pausar y reanudar la búsqueda y el análisis de vacantes en toda la plataforma.

#### Scenario: La aplicación inicia sin una configuración previa
- **WHEN** el sistema consulta el estado operativo y todavía no existe una configuración guardada
- **THEN** la búsqueda y el análisis permanecen habilitados para conservar el comportamiento habitual

#### Scenario: La persona administradora pausa el procesamiento
- **WHEN** la persona administradora apaga el procesamiento global
- **THEN** el sistema guarda el estado pausado, lo muestra en el centro administrativo y no bloquea el acceso al propio centro administrativo

#### Scenario: La persona administradora reanuda el procesamiento
- **WHEN** la persona administradora enciende el procesamiento global
- **THEN** el sistema guarda el estado habilitado y permite continuar los ciclos automáticos

### Requirement: Detener nuevos trabajos mientras el procesamiento está pausado
Mientras la pausa global esté activa, el sistema SHALL impedir que comiencen nuevas búsquedas o análisis automáticos y SHALL conservar el trabajo pendiente para reanudarlo después.

#### Scenario: Vence un ciclo periódico durante la pausa
- **WHEN** llega el horario de una búsqueda o análisis periódico y el procesamiento está pausado
- **THEN** el sistema no inicia el trabajo ni lo contabiliza como una ejecución completada

#### Scenario: Hay trabajos en cola al pausar
- **WHEN** se pausa el procesamiento mientras existen trabajos pendientes que todavía no comenzaron
- **THEN** esos trabajos no comienzan y permanecen pendientes para procesarse después de reanudar

#### Scenario: Un trabajo ya está en curso al pausar
- **WHEN** se activa la pausa durante una búsqueda o análisis ya iniciado
- **THEN** el trabajo en curso puede completar su unidad actual, pero no inicia unidades posteriores mientras la pausa continúe activa

#### Scenario: Se reanuda con trabajo pendiente
- **WHEN** la persona administradora reanuda el procesamiento y hay trabajos pendientes
- **THEN** el sistema permite que continúen por el flujo habitual sin crear duplicados por la pausa

### Requirement: Respetar la pausa en las acciones manuales de procesamiento
El sistema SHALL aplicar la pausa global a las acciones administrativas que inicien búsquedas o análisis de vacantes.

#### Scenario: Se solicita una búsqueda manual durante la pausa
- **WHEN** la persona administradora solicita una actualización de fuentes mientras el procesamiento está pausado
- **THEN** el sistema no inicia la búsqueda e informa que la operación está pausada

#### Scenario: Se registra una vacante por URL durante la pausa
- **WHEN** la persona administradora intenta iniciar el procesamiento de una vacante mediante URL mientras está activa la pausa
- **THEN** el sistema no inicia la extracción ni el análisis e informa que el procesamiento está pausado
