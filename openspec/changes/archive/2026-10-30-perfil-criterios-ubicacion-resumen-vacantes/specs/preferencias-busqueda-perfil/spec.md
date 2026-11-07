# Spec Delta

## Purpose

Permite a cada aspirante expresar y mantener preferencias de búsqueda concretas, combinándolas con sugerencias derivadas de su hoja de vida para encontrar vacantes relevantes.

## ADDED Requirements

### Requirement: Administrar frases de búsqueda
El sistema SHALL permitir que cada aspirante agregue y quite frases independientes que describan cargos, áreas o condiciones de búsqueda.

#### Scenario: Agregar frases al perfil
- **WHEN** el aspirante guarda una o más frases válidas
- **THEN** el sistema conserva cada frase como un elemento separado de su perfil y de la revisión vigente

#### Scenario: Quitar una frase
- **WHEN** el aspirante elimina una frase y guarda el perfil
- **THEN** las próximas búsquedas usan las frases restantes y ninguna revisión nueva conserva la frase eliminada

### Requirement: Definir ubicaciones y trabajo remoto
El sistema SHALL permitir registrar varias ubicaciones de interés y si el aspirante acepta vacantes remotas.

#### Scenario: Buscar en varias ubicaciones
- **WHEN** el perfil incluye una o más ubicaciones
- **THEN** el sistema entrega esas ubicaciones al análisis de compatibilidad de cada vacante

#### Scenario: Aceptar trabajo remoto
- **WHEN** el aspirante activa la preferencia de trabajo remoto
- **THEN** el análisis trata una vacante explícitamente remota como compatible con la ubicación

#### Scenario: No aceptar trabajo remoto
- **WHEN** el aspirante no activa trabajo remoto y la vacante no coincide con sus ubicaciones
- **THEN** el análisis refleja esa diferencia en el puntaje o en los aspectos por revisar

### Requirement: Complementar frases con la hoja de vida
El sistema SHALL complementar las frases del aspirante con términos de búsqueda respaldados por el contenido de su hoja de vida.

#### Scenario: Generar términos complementarios
- **WHEN** el sistema prepara la búsqueda para una revisión de perfil
- **THEN** la IA conserva las frases del aspirante y puede agregar términos concretos sustentados por su hoja de vida

#### Scenario: La IA no encuentra términos adicionales
- **WHEN** la hoja de vida no respalda términos adicionales útiles
- **THEN** el sistema busca con las frases del aspirante sin inventar cargos ni experiencia

### Requirement: Descargar la hoja de vida de forma privada
El sistema SHALL servir la hoja de vida únicamente a su propietario autenticado mediante una ruta de descarga asociada a su perfil.

#### Scenario: El propietario descarga su hoja de vida
- **WHEN** el aspirante autenticado solicita la descarga de su archivo vigente
- **THEN** el sistema devuelve el archivo del perfil

#### Scenario: Otra cuenta intenta acceder al archivo
- **WHEN** una cuenta distinta o una persona no autenticada solicita el archivo privado
- **THEN** el sistema no revela ni entrega el archivo
