# Spec Delta

## MODIFIED Requirements

### Requirement: Actualizar publicaciones ya conocidas
El sistema SHALL actualizar una vacante conocida de una fuente en lugar de crear una segunda publicación visible, y SHALL conservar los seguimientos existentes por perfil al actualizar la publicación.

#### Scenario: La fuente devuelve una publicación ya registrada
- **WHEN** una consulta encuentra una vacante que ya está registrada para esa fuente
- **THEN** el sistema actualiza sus datos disponibles y mantiene un solo registro visible

#### Scenario: La publicación está descartada para un perfil
- **WHEN** una consulta vuelve a encontrar una publicación cuyo seguimiento está descartado para un perfil
- **THEN** el sistema actualiza la vacante compartida sin crear otro seguimiento ni cambiar el estado descartado de ese perfil

#### Scenario: La misma publicación tiene estados distintos por perfil
- **WHEN** la publicación se actualiza y distintos perfiles tienen seguimientos diferentes
- **THEN** el sistema conserva el estado de cada perfil de forma independiente
