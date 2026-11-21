# Spec Delta

## ADDED Requirements

### Requirement: Mantener visibles los análisis anteriores al cambio de perfil
El dashboard SHALL conservar accesible el análisis completado de una vacante para su perfil aunque la revisión o configuración posterior cambie, junto con su trazabilidad y seguimiento.

#### Scenario: Se guarda una revisión nueva
- **WHEN** una persona actualiza su perfil después de completar un análisis
- **THEN** el resultado y seguimiento existentes permanecen accesibles sin reanálisis
