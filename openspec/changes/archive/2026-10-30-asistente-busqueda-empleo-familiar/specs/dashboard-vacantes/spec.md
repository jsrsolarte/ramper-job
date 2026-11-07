# Spec Delta

## Purpose

Presenta a cada persona las vacantes más relevantes para su búsqueda en un dashboard privado, con información suficiente para decidir si desea continuar en la fuente original.

## ADDED Requirements

### Requirement: Vacantes ordenadas por compatibilidad
El dashboard SHALL mostrar las vacantes analizadas de la persona ordenadas desde el puntaje de compatibilidad más alto al más bajo.

#### Scenario: Hay varias vacantes analizadas
- **WHEN** la persona abre su dashboard y tiene varias vacantes analizadas
- **THEN** el sistema las muestra ordenadas por puntaje de compatibilidad descendente

### Requirement: Información organizada de cada vacante
El dashboard SHALL mostrar la descripción organizada por IA, el puntaje de compatibilidad, las razones de coincidencia, los requisitos que no coinciden o no están evidenciados y el enlace a la publicación original.

#### Scenario: Persona consulta una vacante
- **WHEN** la persona abre una vacante del dashboard
- **THEN** ve el contenido organizado por IA y el enlace para consultar la publicación en su fuente

### Requirement: Postulación desde la fuente original
El sistema SHALL dirigir a la persona a la publicación original para continuar con una vacante y SHALL permitirle decidir y realizar la postulación allí.

#### Scenario: Persona desea postularse
- **WHEN** la persona selecciona el enlace de una vacante
- **THEN** el sistema abre la publicación original y no envía una postulación automática
