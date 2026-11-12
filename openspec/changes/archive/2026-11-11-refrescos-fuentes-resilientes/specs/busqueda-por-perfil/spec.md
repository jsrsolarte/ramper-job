# Spec Delta

## MODIFIED Requirements

### Requirement: Buscar vacantes con términos y ubicaciones del perfil
Cada conector compatible SHALL recibir las palabras clave, ubicaciones y modalidad aplicables a una solicitud de búsqueda y devolver las vacantes públicas encontradas, conservando la URL original. El sistema SHALL compartir una consulta entre perfiles cuando esos criterios efectivos sean equivalentes. SHALL completar el conjunto de búsquedas mediante unidades de trabajo acotadas y reanudables, sin omitir combinaciones por exceder el límite de una tarea.

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

#### Scenario: Un perfil genera más trabajo que el límite de una tarea
- **WHEN** las combinaciones de términos, ubicaciones y fichas de una fuente exceden el presupuesto de trabajo de una tarea Celery
- **THEN** el sistema procesa unidades acotadas hasta cubrir todas las combinaciones, sin mantener una sola tarea activa más allá de su límite

#### Scenario: Se reintenta una unidad interrumpida
- **WHEN** una unidad de búsqueda vence o se interrumpe después de guardar parte de sus resultados
- **THEN** el sistema reanuda desde el último punto confirmado y no duplica vacantes, asociaciones, seguimientos ni análisis

### Requirement: Compartir vacantes sin mezclar resultados privados
El sistema SHALL reutilizar una vacante normalizada encontrada por cualquier búsqueda y mantener el análisis independiente para cada perfil activo relacionado con la búsqueda.

#### Scenario: Una publicación coincide con búsquedas de dos perfiles
- **WHEN** una misma vacante aparece en una búsqueda compartida o en consultas distintas de dos perfiles
- **THEN** se conserva una publicación y cada perfil relacionado recibe su propio análisis privado en su dashboard

#### Scenario: Los perfiles tienen rúbricas o decisiones distintas
- **WHEN** dos perfiles comparten una vacante encontrada mediante criterios de búsqueda equivalentes
- **THEN** el sistema evalúa por separado la vacante con la rúbrica vigente de cada perfil y conserva sus estados de seguimiento de forma independiente
