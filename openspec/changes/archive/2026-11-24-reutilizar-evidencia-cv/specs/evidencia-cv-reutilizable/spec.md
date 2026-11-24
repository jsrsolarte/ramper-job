# Spec Delta

## Purpose

Convierte cada revisión del CV en evidencia laboral compacta y reutilizable. Permite orientar búsquedas y analizar vacantes con menos información repetida, conservando el vínculo entre cada afirmación y el documento de origen.

## ADDED Requirements

### Requirement: Extraer evidencia laboral compacta por revisión
El sistema SHALL generar y conservar una representación compacta de hechos laborales respaldados por el CV para cada revisión del perfil.

#### Scenario: Se procesa una revisión nueva del perfil
- **WHEN** una revisión del perfil con CV necesita términos de búsqueda o análisis de vacantes
- **THEN** el sistema extrae una sola representación reutilizable de experiencia, habilidades, logros, estudios y certificaciones presentes en el documento

#### Scenario: Se procesa nuevamente la misma revisión
- **WHEN** se solicita evidencia para una revisión y versión de extractor ya procesadas
- **THEN** el sistema reutiliza la representación conservada sin volver a enviar el CV completo para extraerla

#### Scenario: Cambia el CV del perfil
- **WHEN** la persona guarda una revisión nueva del perfil
- **THEN** las búsquedas y análisis usan evidencia extraída de esa revisión y no la representación de una revisión anterior

### Requirement: Mantener la evidencia fiel y privada
La representación SHALL conservar hechos vinculados a evidencia del CV, SHALL omitir información personal que no sea pertinente para la compatibilidad laboral y SHALL permanecer aislada por perfil.

#### Scenario: El CV incluye datos de contacto o formato accesorio
- **WHEN** el sistema extrae la representación laboral
- **THEN** conserva los hechos laborales útiles y omite datos de contacto, elementos de formato y otros detalles personales ajenos a la evaluación

#### Scenario: Una afirmación se usa en una búsqueda o evaluación
- **WHEN** el sistema presenta una afirmación extraída como evidencia
- **THEN** puede rastrearla hasta el contenido correspondiente de la revisión del CV y no inventa fechas, logros, competencias ni credenciales

#### Scenario: Dos perfiles tienen CV distintos
- **WHEN** el sistema busca o analiza vacantes para una persona
- **THEN** usa solo evidencia derivada de las revisiones de esa persona y no revela ni reutiliza la representación de otra cuenta

### Requirement: Seleccionar evidencia pertinente para cada vacante
El sistema SHALL priorizar para cada análisis la evidencia del perfil relacionada con el cargo, las responsabilidades, los requisitos publicados y los criterios de la rúbrica vigente.

#### Scenario: Vacante con requisitos relacionados con el perfil
- **WHEN** se analiza una vacante con requisitos, responsabilidades o habilidades que coinciden con hechos del perfil
- **THEN** el modelo recibe esos hechos relevantes organizados para evaluar los criterios aplicables de la rúbrica

#### Scenario: La selección no cubre claramente un criterio aplicable
- **WHEN** la evidencia seleccionada no permite evaluar con suficiente contexto un criterio aplicable
- **THEN** el sistema amplía la evidencia enviada con hechos adicionales de la representación compacta antes de concluir que falta evidencia

#### Scenario: El CV contiene requisitos o credenciales pertinentes
- **WHEN** la vacante establece requisitos obligatorios de educación, certificación o experiencia y el CV contiene hechos relacionados
- **THEN** la selección conserva esos hechos para que la evaluación pueda confirmarlos o identificar contradicciones explícitas

### Requirement: Reutilizar la representación en búsqueda y análisis
El sistema SHALL usar la representación conservada para generar términos de búsqueda y analizar vacantes, y SHALL NOT enviar el CV completo en cada análisis posterior.

#### Scenario: Se generan términos de búsqueda
- **WHEN** el sistema necesita sugerir términos para una revisión del perfil
- **THEN** utiliza la representación laboral reutilizable junto con las preferencias de búsqueda vigentes

#### Scenario: Se analiza una vacante
- **WHEN** el sistema solicita un análisis de compatibilidad para una revisión del perfil
- **THEN** utiliza la evidencia seleccionada para esa vacante en lugar de volver a enviar el texto completo del CV

#### Scenario: Falla la extracción de evidencia
- **WHEN** no se puede generar una representación válida para la revisión vigente
- **THEN** el sistema conserva la búsqueda o análisis para reintento y no sustituye la evidencia faltante con información de otra revisión
