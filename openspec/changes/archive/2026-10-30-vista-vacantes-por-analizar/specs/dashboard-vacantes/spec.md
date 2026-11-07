# Spec Delta

## ADDED Requirements

### Requirement: Consultar vacantes en espera de análisis
El dashboard SHALL ofrecer una vista privada de las vacantes cuyos análisis están pendientes para el perfil vigente de la persona.

#### Scenario: Hay análisis pendientes para el perfil vigente
- **WHEN** la persona abre la vista de vacantes por analizar
- **THEN** el sistema muestra las vacantes asociadas a análisis pendientes de su perfil y revisión vigente

#### Scenario: El análisis pertenece a otra persona o revisión
- **WHEN** una vacante tiene un análisis pendiente para otro perfil o una revisión anterior
- **THEN** el sistema no la incluye en la vista del perfil actual

#### Scenario: No hay vacantes en espera de análisis
- **WHEN** la persona abre la vista y no tiene análisis pendientes vigentes
- **THEN** el sistema muestra un estado vacío que indica que no hay vacantes por analizar

### Requirement: Presentar los datos originales de vacantes pendientes
La vista de vacantes por analizar SHALL presentar los datos originales disponibles de la publicación sin atribuirle resultados generados por IA.

#### Scenario: Vacante pendiente con datos disponibles
- **WHEN** la vista muestra una vacante cuyo análisis sigue pendiente
- **THEN** presenta su cargo, empresa, ubicación, fuente, descripción original disponible y enlace a la publicación, y no muestra puntaje ni resumen generado por IA

#### Scenario: Vacante pendiente con datos incompletos
- **WHEN** la publicación no contiene alguno de los datos mostrables
- **THEN** la vista omite ese dato o lo marca como no informado sin inventarlo

### Requirement: Navegar entre vacantes recomendadas y pendientes de análisis
El dashboard SHALL presentar las vacantes por analizar y las recomendaciones como pestañas de una misma experiencia privada de vacantes.

#### Scenario: La persona abre la pestaña de análisis pendiente
- **WHEN** la persona selecciona la pestaña «Por analizar»
- **THEN** el sistema muestra las vacantes pendientes del perfil actual sin cambiar el estado técnico de ningún análisis

#### Scenario: La persona abre las recomendaciones
- **WHEN** la persona selecciona la pestaña «Recomendaciones»
- **THEN** el sistema muestra las recomendaciones disponibles del perfil actual sin alterar los análisis pendientes

### Requirement: Mostrar el conteo de vacantes por analizar
La pestaña «Por analizar» SHALL mostrar el conteo de vacantes únicas pendientes para el perfil y revisión vigentes.

#### Scenario: Hay vacantes pendientes
- **WHEN** existen vacantes pendientes de análisis para el perfil y revisión vigentes
- **THEN** el conteo de «Por analizar» coincide con el número de vacantes únicas que muestra la pestaña

#### Scenario: No hay vacantes pendientes
- **WHEN** no existen vacantes pendientes de análisis para el perfil y revisión vigentes
- **THEN** la pestaña muestra el conteo cero
