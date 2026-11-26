# Spec Delta

## MODIFIED Requirements

### Requirement: Configuración ajustable y versionada
El sistema SHALL permitir a una persona administradora ajustar y versionar los prompts y parámetros usados para generar búsquedas y evaluar compatibilidad.

#### Scenario: Administrador modifica la configuración
- **WHEN** una persona administradora guarda cambios en un prompt o parámetro
- **THEN** el sistema crea una nueva versión para los procesos siguientes sin alterar los resultados ya generados

#### Scenario: Se reprocesa una vacante
- **WHEN** una persona administradora solicita procesar una vacante con análisis completado para ese perfil
- **THEN** el sistema conserva el resultado y no solicita un nuevo análisis

## ADDED Requirements

### Requirement: Conservar análisis completados por perfil
El sistema SHALL reutilizar el análisis completado de una vacante para un perfil sin reevaluarlo por cambios posteriores del perfil, configuración o ficha. Un perfil sin resultado completado SHALL usar su revisión vigente.

#### Scenario: Cambia el perfil después del análisis
- **WHEN** una persona modifica su perfil tras completarse un análisis
- **THEN** el resultado previo sigue visible con su revisión original y no se reanaliza

#### Scenario: Una vacante conocida corresponde a otro perfil
- **WHEN** otro perfil elegible aún no tiene un análisis completado para la vacante
- **THEN** el sistema evalúa ese perfil con su revisión vigente usando la ficha guardada

#### Scenario: Varias tareas coinciden
- **WHEN** varias búsquedas encuentran la misma URL para el mismo perfil al mismo tiempo
- **THEN** el sistema evita crear o ejecutar análisis duplicados
