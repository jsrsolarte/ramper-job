# Spec Delta

## REMOVED Requirements

### Requirement: Consultar la disponibilidad de publicaciones
El panel SHALL mostrar por separado el número de publicaciones activas y cerradas, sin confundir disponibilidad de la fuente con el estado personal de seguimiento.

#### Scenario: Hay publicaciones abiertas y cerradas
- **WHEN** existen publicaciones con ambos estados de disponibilidad
- **THEN** el panel muestra sus conteos como una dimensión separada de los estados de seguimiento

#### Scenario: Una publicación no tiene comprobación concluyente
- **WHEN** la disponibilidad de una publicación es desconocida o su comprobación no fue concluyente
- **THEN** el panel la presenta en una categoría separada y no la cuenta como cerrada

**Reason**: La aplicación no verificará de forma continua si Elempleo mantiene o cierra una publicación, por lo que estos conteos no son una medida confiable que debamos mostrar.

**Migration**: Retirar los conteos de disponibilidad de la vista de estadísticas. Conservar separados los estados personales de seguimiento; descartar una vacante no significa que la publicación esté cerrada.
