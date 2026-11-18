# Spec Delta

## ADDED Requirements

### Requirement: Usar solo la rúbrica vigente en análisis nuevos
El sistema SHALL usar exclusivamente la rúbrica vigente de cinco estrellas para todo análisis nuevo y SHALL conservar los resultados anteriores solo como historial, sin recalcularlos ni modificarlos.

#### Scenario: Se crea un análisis nuevo
- **WHEN** el sistema solicita una evaluación de compatibilidad
- **THEN** solicita la rúbrica vigente de 0 a 5 puntos en incrementos de medio punto y rechaza respuestas identificadas con otra versión

#### Scenario: Se consulta un análisis histórico
- **WHEN** la persona consulta un análisis creado con una versión anterior de la rúbrica
- **THEN** el sistema presenta los valores y el desglose almacenados sin reevaluarlos ni usar esa versión para análisis nuevos
