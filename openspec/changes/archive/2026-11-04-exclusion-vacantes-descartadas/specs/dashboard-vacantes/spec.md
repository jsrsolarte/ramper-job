# Spec Delta

## ADDED Requirements

### Requirement: Mantener vacantes descartadas fuera de Recomendaciones
El dashboard SHALL excluir de Recomendaciones y de su conteo las vacantes que el perfil actual haya descartado, aunque la vacante vuelva a ingerirse o tenga un análisis nuevo. El descarte SHALL permanecer vigente hasta que la persona restaure explícitamente la vacante.

#### Scenario: Se vuelve a analizar una vacante descartada
- **WHEN** una vacante descartada para el perfil actual recibe un análisis nuevo o actualizado
- **THEN** el dashboard la mantiene fuera de Recomendaciones y no cambia su seguimiento descartado

#### Scenario: Una búsqueda vuelve a encontrar la vacante descartada
- **WHEN** la ingesta encuentra nuevamente una vacante descartada para el perfil actual
- **THEN** la vacante no reaparece como recomendación y el conteo de Recomendaciones no aumenta por ella

#### Scenario: El seguimiento descartado está archivado
- **WHEN** una vacante descartada y archivada se ingiere o analiza de nuevo
- **THEN** el sistema no crea otro seguimiento pendiente y la mantiene fuera de Recomendaciones

#### Scenario: Otro perfil no descartó la vacante
- **WHEN** un perfil descartó una vacante compartida y otro perfil tiene un seguimiento no descartado para esa misma vacante
- **THEN** el dashboard del segundo perfil sigue mostrando la vacante según su propio estado y puntaje

#### Scenario: La persona restaura la vacante
- **WHEN** la persona restaura explícitamente una vacante descartada
- **THEN** el sistema recupera el estado previo al descarte y la muestra en el listado correspondiente
