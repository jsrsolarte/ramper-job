# Spec Delta

## ADDED Requirements

### Requirement: Informar cobertura tras una limpieza administrativa
El sistema SHALL mostrar el inicio de la nueva cobertura operativa después de una limpieza, sin presentar el historial eliminado como actividad cero.

#### Scenario: Se consulta un periodo que precede la limpieza
- **WHEN** una persona administradora consulta métricas cuyo periodo incluye datos eliminados
- **THEN** el panel informa que el historial anterior no está disponible y muestra desde cuándo existe cobertura posterior
