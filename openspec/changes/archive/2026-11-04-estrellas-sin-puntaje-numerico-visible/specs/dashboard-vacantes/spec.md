# Spec Delta

## ADDED Requirements

### Requirement: Mostrar solo estrellas como puntaje visible en la tarjeta
El dashboard SHALL mostrar el puntaje de compatibilidad de cada tarjeta con estrellas y SHALL NOT mostrar junto a ellas la fracción numérica sobre 10, manteniendo el valor exacto en la etiqueta accesible.

#### Scenario: Persona consulta una recomendación
- **WHEN** una tarjeta muestra una vacante con puntaje calculado
- **THEN** se ven las estrellas sin una fracción como «7/10» debajo o al lado

#### Scenario: Se consulta con tecnología de asistencia
- **WHEN** una tecnología de asistencia lee el puntaje de una tarjeta
- **THEN** se anuncia el puntaje numérico exacto y su equivalencia visual en estrellas

#### Scenario: El puntaje se usa en filtros y orden
- **WHEN** el sistema filtra u ordena vacantes por compatibilidad
- **THEN** usa el puntaje numérico exacto sin depender de la presentación visual en estrellas
