# Spec Delta

## ADDED Requirements

### Requirement: Distinguir fichas reutilizadas de solicitudes
El panel SHALL distinguir por consulta las fichas reutilizadas de las solicitudes y respuestas reales de detalle sin exponer información privada.

#### Scenario: Una consulta mezcla fichas nuevas y conocidas
- **WHEN** el sistema reutiliza algunas fichas y solicita otras
- **THEN** muestra conteos separados y no presenta la reutilización como una solicitud de red

#### Scenario: Historial anterior a la medición
- **WHEN** una consulta histórica no dispone de la nueva métrica
- **THEN** el panel indica que no está disponible y no infiere cero
