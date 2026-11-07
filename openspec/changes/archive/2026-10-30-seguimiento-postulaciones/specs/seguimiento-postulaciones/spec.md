# Spec Delta

## Purpose

Permite a cada persona organizar las oportunidades de su perfil según una secuencia de postulación y conservar el resultado final de cada proceso. El seguimiento se conserva aunque la vacante vuelva a analizarse con una revisión o configuración de IA nueva.

## ADDED Requirements

### Requirement: Registrar un estado personal por vacante
El sistema SHALL conservar por separado para cada perfil y vacante un estado de seguimiento, independiente del estado y las versiones del análisis de IA.

#### Scenario: Se crea seguimiento para una vacante recomendada
- **WHEN** una vacante aparece como recomendación de un perfil y aún no tiene seguimiento
- **THEN** el sistema la considera pendiente de decisión para ese perfil

#### Scenario: Dos perfiles siguen la misma publicación
- **WHEN** dos perfiles tienen análisis de la misma vacante
- **THEN** cada perfil puede mantener un estado de seguimiento distinto

#### Scenario: Se reprocesa el análisis
- **WHEN** se crea un análisis nuevo para la misma vacante y perfil
- **THEN** el estado de seguimiento existente se conserva

### Requirement: Cambiar el estado de seguimiento de una vacante
El sistema SHALL permitir avanzar una vacante únicamente por estas etapas: pendiente de decisión, aplicada, en proceso y entrevista. Desde aplicada, en proceso o entrevista, la persona también puede marcar el proceso como finalizado. El sistema SHALL rechazar cualquier transición que salte o retroceda etapas.

#### Scenario: La persona inicia una postulación
- **WHEN** la persona cambia una vacante pendiente de decisión a aplicada
- **THEN** el sistema guarda ese estado para su perfil y muestra la vacante en aplicadas

#### Scenario: La postulación avanza de forma secuencial
- **WHEN** la persona cambia una vacante aplicada a en proceso o una vacante en proceso a entrevista
- **THEN** el sistema guarda la etapa siguiente y muestra la vacante en el listado correspondiente

#### Scenario: El proceso termina sin continuar
- **WHEN** la persona marca como finalizado un proceso en estado aplicada, en proceso o entrevista
- **THEN** el sistema guarda la vacante como finalizada y la muestra en ese listado

#### Scenario: Se intenta saltar o retroceder una etapa
- **WHEN** la persona intenta mover una vacante a una etapa que no es la siguiente permitida
- **THEN** el sistema rechaza el cambio y conserva el estado de seguimiento vigente

#### Scenario: El seguimiento no cambia el análisis de IA
- **WHEN** la persona avanza una vacante por el flujo de postulación
- **THEN** el sistema conserva sin cambios el estado técnico y el resultado del análisis de IA

### Requirement: Descartar una vacante desde cualquier estado
El sistema SHALL permitir que la persona descarte una vacante desde cualquier estado, incluido finalizada, y conservar el estado que tenía inmediatamente antes del descarte.

#### Scenario: La persona descarta una vacante en cualquier etapa
- **WHEN** la persona descarta una vacante pendiente, aplicada, en proceso, en entrevista o finalizada
- **THEN** el sistema la muestra como descartada y conserva la etapa previa para poder restaurarla

### Requirement: Restaurar una vacante descartada
El sistema SHALL permitir restaurar una vacante descartada al estado que tenía inmediatamente antes de descartarse.

#### Scenario: La persona restaura una vacante descartada
- **WHEN** la persona restaura una vacante descartada
- **THEN** el sistema recupera su estado previo al descarte y vuelve a incluirla en el listado correspondiente
