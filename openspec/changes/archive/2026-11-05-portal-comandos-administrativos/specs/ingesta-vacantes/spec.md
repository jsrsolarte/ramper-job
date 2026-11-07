# Spec Delta

## ADDED Requirements

### Requirement: Permitir una actualización manual de fuentes
El sistema SHALL permitir a la persona administradora iniciar una actualización de fuentes antes del siguiente ciclo periódico, usando el flujo habitual de búsqueda, deduplicación y análisis elegible.

#### Scenario: Administración inicia una actualización antes del horario
- **WHEN** la persona administradora solicita actualizar fuentes antes de que venza el intervalo automático de 120 minutos
- **THEN** el sistema encola la actualización inmediatamente sin esperar al siguiente ciclo y conserva el horario periódico configurado

#### Scenario: La búsqueda encuentra una vacante nueva elegible
- **WHEN** la actualización manual encuentra una vacante que no está registrada y cumple las condiciones del perfil
- **THEN** el sistema crea un único registro y encola el análisis correspondiente

#### Scenario: La búsqueda encuentra una vacante ya analizada
- **WHEN** la actualización manual vuelve a encontrar una vacante que ya tiene registro y análisis completado
- **THEN** el sistema actualiza el mismo registro si corresponde y no crea otra vacante ni duplica el análisis por el solo hecho de repetir la búsqueda

#### Scenario: Ya hay una actualización periódica o manual en curso
- **WHEN** la persona administradora solicita una actualización mientras otra ejecución equivalente sigue activa
- **THEN** el sistema informa la ejecución existente y no inicia una búsqueda concurrente duplicada
