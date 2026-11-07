# Spec Delta

## Purpose

Encuentra vacantes a partir de los cargos y habilidades relevantes para cada perfil, y conecta esas búsquedas con el flujo común de deduplicación y análisis privado.

## ADDED Requirements

### Requirement: Derivar palabras clave desde cada perfil
El sistema SHALL generar con la configuración de IA vigente un conjunto acotado de palabras clave laborales usando el CV y los criterios de búsqueda de la revisión vigente de cada perfil.

#### Scenario: Perfil con CV y criterios vigentes
- **WHEN** se inicia una actualización para un perfil activo
- **THEN** el modelo devuelve palabras clave estructuradas y relacionadas con los cargos, habilidades o sectores respaldados por ese CV y esos criterios

#### Scenario: OmniRoute no está disponible
- **WHEN** no se puede generar el conjunto de palabras clave
- **THEN** el sistema registra el fallo para reintento y conserva los resultados ya guardados sin iniciar una búsqueda general sin relación con el perfil

### Requirement: Ajustar la generación de palabras clave
El administrador SHALL poder ajustar y versionar el prompt que genera palabras clave, y el sistema SHALL usar la versión activa en las nuevas búsquedas.

#### Scenario: Se activa una nueva versión del prompt
- **WHEN** el administrador guarda una nueva configuración con otro prompt de búsqueda
- **THEN** la siguiente actualización usa el prompt de la nueva versión para generar términos

### Requirement: Buscar vacantes con términos del perfil
Cada conector compatible SHALL recibir las palabras clave del perfil y devolver las vacantes públicas encontradas para esos términos, conservando la URL original de cada publicación.

#### Scenario: Elempleo recibe una búsqueda específica
- **WHEN** el conjunto de palabras clave contiene “procesos”
- **THEN** el conector consulta la ruta pública de búsqueda de Elempleo correspondiente a “trabajo-procesos” y normaliza las vacantes visibles

#### Scenario: Varias palabras clave encuentran la misma vacante
- **WHEN** más de una consulta devuelve el mismo enlace de publicación
- **THEN** el sistema conserva una sola vacante y evita duplicar su análisis para el mismo perfil y revisión

### Requirement: Compartir vacantes sin mezclar resultados privados
El sistema SHALL reutilizar una vacante normalizada encontrada por cualquier búsqueda y SHALL crear o mostrar su análisis de manera independiente para cada perfil activo.

#### Scenario: Una publicación coincide con búsquedas de dos perfiles
- **WHEN** una misma vacante aparece en consultas de dos familiares
- **THEN** se conserva una publicación y cada familiar recibe su propio análisis, visible solo en su dashboard
