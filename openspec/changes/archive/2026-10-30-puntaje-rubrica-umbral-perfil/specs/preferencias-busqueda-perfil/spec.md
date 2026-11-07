# Spec Delta

## ADDED Requirements

### Requirement: Definir un puntaje mínimo por perfil
El sistema SHALL permitir que cada aspirante seleccione y guarde en su perfil un puntaje mínimo entero entre 0 y 10 para filtrar las vacantes del dashboard.

#### Scenario: Guardar el puntaje mínimo
- **WHEN** el aspirante selecciona un valor entre 0 y 10 y guarda el perfil
- **THEN** el sistema conserva ese umbral para el perfil y lo aplica en las siguientes consultas del dashboard

#### Scenario: Perfil sin umbral configurado
- **WHEN** un perfil todavía no tiene un umbral guardado
- **THEN** el sistema aplica 0 como puntaje mínimo y no oculta vacantes por puntaje

#### Scenario: Valor fuera de rango
- **WHEN** se intenta guardar un valor menor que 0, mayor que 10 o no entero
- **THEN** el sistema rechaza el valor e informa que el umbral debe ser un entero de 0 a 10

### Requirement: Cambiar el umbral sin reanalizar vacantes
El sistema SHALL aplicar el puntaje mínimo como filtro de presentación y SHALL NOT solicitar nuevos análisis de IA únicamente porque cambie ese valor.

#### Scenario: Aspirante ajusta el mínimo
- **WHEN** el aspirante cambia y guarda el puntaje mínimo
- **THEN** el dashboard filtra los análisis existentes según el nuevo valor sin encolar análisis ni modificar sus puntajes
