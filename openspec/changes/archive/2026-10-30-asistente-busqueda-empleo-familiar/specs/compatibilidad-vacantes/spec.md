# Spec Delta

## Purpose

Evalúa qué tan bien se ajusta una vacante al CV y los criterios de una persona, y prepara una explicación legible para apoyar su búsqueda laboral.

## ADDED Requirements

### Requirement: Análisis por perfil mediante el servicio de IA
El sistema SHALL solicitar al modelo de IA configurado mediante OmniRoute que analice cada vacante según el CV y los criterios del perfil correspondiente.

#### Scenario: Vacante analizada para un perfil
- **WHEN** existe una vacante nueva y un perfil con CV y criterios vigentes
- **THEN** el sistema solicita un análisis de compatibilidad para ese perfil

#### Scenario: Servicio de IA no disponible
- **WHEN** OmniRoute o el modelo configurado no devuelve un análisis utilizable
- **THEN** el sistema no inventa una clasificación y marca la vacante como pendiente de análisis

### Requirement: Resultado explicable de compatibilidad
El sistema SHALL conservar para cada análisis un puntaje de compatibilidad de 0 a 100, razones que coinciden con el perfil y requisitos que no coinciden o no están evidenciados en el CV.

#### Scenario: Análisis completo
- **WHEN** el modelo devuelve un análisis válido
- **THEN** el resultado incluye un puntaje, razones de coincidencia y requisitos que no coinciden o no están evidenciados

### Requirement: Descripción organizada por IA
El sistema SHALL generar una descripción organizada de la vacante para presentarla a la persona, diferenciándola del contenido original de la fuente.

#### Scenario: Descripción organizada disponible
- **WHEN** el análisis de una vacante termina correctamente
- **THEN** el sistema guarda una descripción organizada por IA basada en la información obtenida de la publicación

### Requirement: Configuración ajustable y versionada
El sistema SHALL permitir que una persona administradora ajuste los prompts y parámetros de coincidencia usados por el análisis, conserve cada versión y registre qué versiones se utilizaron para cada resultado.

#### Scenario: Administrador modifica el análisis
- **WHEN** una persona administradora guarda cambios en un prompt o en los parámetros de coincidencia
- **THEN** el sistema crea una nueva versión de configuración que se aplica a los análisis siguientes sin alterar los resultados ya generados

#### Scenario: Se reprocesa una vacante
- **WHEN** una persona administradora solicita reprocesar una vacante para un perfil
- **THEN** el sistema genera un nuevo análisis usando la versión vigente del perfil, prompt y parámetros, y conserva el resultado previo para consulta o trazabilidad
