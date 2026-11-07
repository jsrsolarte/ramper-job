# Búsqueda por perfil Specification

## Purpose

Encuentra vacantes a partir de los cargos y habilidades relevantes para cada perfil y conecta esas búsquedas con el flujo común de ingesta y análisis privado.

## Requirements

### Requirement: Derivar palabras clave desde cada perfil
El sistema SHALL generar con la configuración de IA vigente un conjunto acotado de palabras clave laborales usando el CV y las preferencias de la revisión vigente.

#### Scenario: Perfil con CV y preferencias vigentes
- **WHEN** se inicia una actualización para un perfil activo
- **THEN** el modelo devuelve palabras clave relacionadas con cargos, habilidades o sectores respaldados por el CV y las preferencias

#### Scenario: OmniRoute no está disponible
- **WHEN** no se puede generar el conjunto de palabras clave
- **THEN** el sistema registra el fallo para reintento, conserva los resultados guardados y no inicia una búsqueda general sin relación con el perfil

### Requirement: Ajustar la generación de palabras clave
El administrador SHALL poder ajustar y versionar el prompt que genera palabras clave, y el sistema SHALL usar la versión activa en las nuevas búsquedas.

#### Scenario: Se activa una nueva versión del prompt
- **WHEN** el administrador guarda una nueva configuración de búsqueda
- **THEN** la siguiente actualización usa esa versión para generar términos

### Requirement: Buscar vacantes con términos y ubicaciones del perfil
Cada conector compatible SHALL recibir las palabras clave, ubicaciones y modalidad aplicables a una solicitud de búsqueda y devolver las vacantes públicas encontradas, conservando la URL original. El sistema SHALL compartir una consulta entre perfiles cuando esos criterios efectivos sean equivalentes.

#### Scenario: Elempleo recibe una búsqueda específica
- **WHEN** el conjunto contiene el término «procesos» y una ubicación aplicable
- **THEN** el conector consulta la búsqueda pública de Elempleo combinando el término y el filtro geográfico

#### Scenario: Dos perfiles tienen criterios de búsqueda equivalentes
- **WHEN** dos perfiles vigentes generan las mismas palabras clave, ubicaciones aplicables y modalidad remota para una fuente
- **THEN** el sistema realiza una sola consulta equivalente a esa fuente y asocia cada vacante encontrada con ambos perfiles

#### Scenario: Perfiles distintos requieren consultas distintas
- **WHEN** las palabras clave, ubicaciones aplicables o modalidad remota difieren entre dos perfiles
- **THEN** el sistema conserva solicitudes de búsqueda separadas para los criterios que difieren

#### Scenario: Varias consultas encuentran la misma vacante
- **WHEN** más de una consulta devuelve la misma publicación
- **THEN** el sistema conserva una sola vacante y evita duplicar su análisis para el mismo perfil y revisión

### Requirement: Compartir vacantes sin mezclar resultados privados
El sistema SHALL reutilizar una vacante normalizada encontrada por cualquier búsqueda y mantener el análisis independiente para cada perfil activo relacionado con la búsqueda.

#### Scenario: Una publicación coincide con búsquedas de dos perfiles
- **WHEN** una misma vacante aparece en una búsqueda compartida o en consultas distintas de dos perfiles
- **THEN** se conserva una publicación y cada perfil relacionado recibe su propio análisis privado en su dashboard

#### Scenario: Los perfiles tienen rúbricas o decisiones distintas
- **WHEN** dos perfiles comparten una vacante encontrada mediante criterios de búsqueda equivalentes
- **THEN** el sistema evalúa por separado la vacante con la rúbrica vigente de cada perfil y conserva sus estados de seguimiento de forma independiente
