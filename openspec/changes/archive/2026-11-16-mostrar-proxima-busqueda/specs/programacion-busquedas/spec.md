# Spec Delta

## Purpose

Permite consultar cuándo se espera el siguiente ciclo automático global de búsqueda de vacantes. La información sirve tanto a las personas aspirantes como a la administración y refleja el intervalo y el estado operativo vigentes.

## ADDED Requirements

### Requirement: Consultar la próxima búsqueda automática
El sistema SHALL mostrar la fecha y hora local estimadas del siguiente ciclo automático global en el dashboard de aspirantes y en el centro administrativo.

#### Scenario: La persona aspirante consulta el dashboard
- **WHEN** el procesamiento está habilitado y existe una estimación válida
- **THEN** el dashboard muestra cuándo se espera la próxima búsqueda automática global

#### Scenario: La persona administradora consulta el centro
- **WHEN** la cuenta administradora abre el centro administrativo y existe una estimación válida
- **THEN** el centro muestra la misma fecha y hora estimadas que consulta una persona aspirante

#### Scenario: No existe una estimación confiable
- **WHEN** el sistema no cuenta con información suficiente para calcular la próxima ejecución automática
- **THEN** ambas vistas indican que el horario todavía no está disponible y no inventan una fecha

### Requirement: Reflejar la pausa y el intervalo vigentes
El horario informado SHALL usar el intervalo automático vigente y SHALL indicar el estado pausado cuando la búsqueda automática no pueda comenzar.

#### Scenario: El procesamiento está pausado
- **WHEN** la persona consulta el horario mientras la pausa global está activa
- **THEN** ambas vistas indican que las búsquedas están pausadas y no presentan una fecha como si el ciclo fuera a ejecutarse

#### Scenario: Cambia el intervalo automático
- **WHEN** la administración modifica el intervalo de actualización de fuentes
- **THEN** la estimación refleja el intervalo vigente para el siguiente ciclo automático

### Requirement: Distinguir el ciclo automático de otras búsquedas
El sistema SHALL identificar el horario como una estimación del ciclo automático global y SHALL explicar que otras acciones pueden iniciar búsquedas antes.

#### Scenario: Una búsqueda puede comenzar antes
- **WHEN** el dashboard o el centro administrativo muestra la próxima búsqueda automática
- **THEN** también aclara que una actualización manual o un cambio de perfil puede iniciar búsquedas antes de ese horario

#### Scenario: Se inicia una actualización manual
- **WHEN** la administración solicita una actualización manual
- **THEN** la hora de esa solicitud no se presenta como el horario del siguiente ciclo automático
