# Spec Delta

## ADDED Requirements

### Requirement: Ocultar seguimientos archivados
El dashboard SHALL excluir de las pestañas y sus conteos los seguimientos archivados del perfil actual.

#### Scenario: El estado del perfil está archivado
- **WHEN** un seguimiento archivado pertenece al perfil actual
- **THEN** la vacante deja de aparecer en las recomendaciones o pestañas de seguimiento de ese perfil y no se incluye en sus conteos

#### Scenario: Otro perfil conserva la vacante activa
- **WHEN** el seguimiento de una vacante se archiva para un perfil pero sigue activo para otro
- **THEN** el dashboard del otro perfil conserva la vacante en su estado y conteo correspondientes

#### Scenario: El registro de vacante se conserva
- **WHEN** se oculta un seguimiento archivado
- **THEN** la vacante compartida y los datos de análisis permanecen almacenados
