# Spec Delta

## ADDED Requirements

### Requirement: Reflejar el descarte automático de recomendaciones
El dashboard SHALL mostrar en Descartadas las recomendaciones vencidas que el proceso automático cambie de estado para el perfil actual.

#### Scenario: La tarea descarta una recomendación vencida
- **WHEN** una recomendación del perfil actual cumple siete días y la tarea diaria la descarta
- **THEN** deja de aparecer en Recomendaciones, aparece en Descartadas y se actualizan los conteos de ambas pestañas

#### Scenario: La persona restaura una recomendación vencida
- **WHEN** la persona restaura desde Descartadas una vacante descartada automáticamente
- **THEN** vuelve a aparecer en Recomendaciones y su conteo refleja el cambio
