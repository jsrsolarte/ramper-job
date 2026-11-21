# estadisticas-individuales-usuarios Specification

## Purpose

Permite a la administración comprender la situación y actividad disponible de un aspirante activo mediante estadísticas individuales.

## Requirements

### Requirement: Acceder a las estadísticas de un aspirante activo
El centro administrativo SHALL ofrecer desde la gestión de usuarios una ficha de estadísticas para cada aspirante activo, identificando claramente la cuenta seleccionada.

#### Scenario: Se selecciona un usuario activo
- **WHEN** la administración selecciona las estadísticas de un aspirante activo
- **THEN** el sistema muestra su ficha individual y permite regresar a la gestión de usuarios

#### Scenario: La cuenta no está disponible
- **WHEN** la administración solicita una cuenta inexistente, administrativa o inactiva
- **THEN** el sistema no muestra estadísticas individuales de esa cuenta e informa que no están disponibles

### Requirement: Proteger la consulta individual
El sistema SHALL restringir la ficha y sus datos a la administración autorizada.

#### Scenario: Una persona no autorizada solicita una ficha
- **WHEN** una persona sin privilegios administrativos solicita estadísticas individuales
- **THEN** el sistema deniega el acceso sin revelar si la cuenta objetivo existe ni sus datos

### Requirement: Mostrar los estados actuales de las vacantes
La ficha SHALL mostrar conteos individuales por estado de seguimiento coherentes con el dashboard del aspirante, sin aplicar filtros temporales ni de puntuación, e indicar la fecha de consulta.

#### Scenario: Hay vacantes en distintos estados
- **WHEN** se consulta un perfil con vacantes visibles en el dashboard
- **THEN** la ficha muestra pendiente de decisión, descartada, aplicada, en proceso, entrevista y finalizada, incluyendo cero en estados vacíos y el total de vacantes contadas

#### Scenario: Hay pendientes sin registro explícito
- **WHEN** una vacante vigente visible carece de seguimiento explícito
- **THEN** se cuenta como pendiente de decisión, igual que en el dashboard

#### Scenario: Hay seguimientos archivados
- **WHEN** existen vacantes archivadas por inactividad
- **THEN** se excluyen de los conteos visibles y se muestra separadamente su cantidad total archivada

### Requirement: Mostrar el procesamiento de análisis
La ficha SHALL mostrar por separado los análisis pendientes, completos y fallidos del perfil, con una definición visible de la unidad contada y sin confundirlos con los estados de seguimiento.

#### Scenario: Existen revisiones de análisis
- **WHEN** una vacante tiene varios análisis
- **THEN** la ficha cuenta como máximo el análisis vigente por vacante y perfil, excluye los reemplazados y explica esta cobertura

#### Scenario: No existen análisis
- **WHEN** el perfil no tiene análisis vigentes
- **THEN** la ficha muestra cero para cada estado técnico

### Requirement: Mostrar actividad histórica disponible
La ficha SHALL mostrar el total de vacantes descubiertas y la fecha del descubrimiento más reciente, además del total de análisis completados históricos y la fecha de finalización más reciente, identificando las unidades y fechas utilizadas.

#### Scenario: Hay registros históricos
- **WHEN** existen descubrimientos o análisis completados del perfil
- **THEN** la ficha muestra sus totales y fechas más recientes, incluidos análisis históricos reemplazados en el total de análisis

#### Scenario: Falta historial
- **WHEN** no existen registros de una categoría
- **THEN** la ficha muestra cero y una indicación de fecha no disponible, sin inferir actividad anterior

#### Scenario: Se consulta la trayectoria de seguimiento
- **WHEN** se presenta la actividad histórica
- **THEN** la ficha aclara que no dispone de una cronología completa de cambios de estado y no presenta el estado actual como historial de transiciones

### Requirement: Informar ausencia de perfil y limitar datos expuestos
La ficha SHALL indicar cuando la cuenta no tiene perfil y mostrar únicamente las métricas definidas, sin exponer CV, prompts, contenido de vacantes ni mensajes técnicos de error.

#### Scenario: La cuenta aún no tiene perfil
- **WHEN** se consulta un aspirante activo sin perfil
- **THEN** la ficha informa que todavía no hay perfil y no atribuye métricas de otra cuenta
