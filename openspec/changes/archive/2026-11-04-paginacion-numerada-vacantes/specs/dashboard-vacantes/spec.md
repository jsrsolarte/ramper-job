# Spec Delta

## ADDED Requirements

### Requirement: Saltar directamente a una página del listado
El dashboard SHALL mostrar números de página en los listados de vacantes paginados y permitir navegar directamente a la página seleccionada, conservando la pestaña y los filtros activos.

#### Scenario: La persona selecciona un número de página
- **WHEN** la persona elige un número distinto de la página actual
- **THEN** el listado muestra las vacantes de la página elegida sin navegar página por página

#### Scenario: Se conserva el estado y los filtros
- **WHEN** la persona salta a otra página con una pestaña de seguimiento o filtro de puntaje activo
- **THEN** el listado mantiene la pestaña y los filtros seleccionados

#### Scenario: La página actual está identificada
- **WHEN** se presenta la navegación numerada
- **THEN** el número de la página actual se distingue visualmente y se identifica como actual para tecnologías de asistencia

#### Scenario: El listado tiene muchas páginas
- **WHEN** el total de páginas es demasiado amplio para mostrar todos los números de forma legible
- **THEN** la navegación muestra un conjunto compacto que incluye páginas cercanas a la actual, acceso a la primera y última página, y una indicación de los intervalos omitidos

#### Scenario: El listado cabe en una sola página
- **WHEN** el total de resultados ocupa una sola página
- **THEN** el listado no muestra controles de paginación innecesarios
