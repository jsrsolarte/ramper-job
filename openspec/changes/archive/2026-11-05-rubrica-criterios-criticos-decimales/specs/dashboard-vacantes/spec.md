# Spec Delta

## MODIFIED Requirements

### Requirement: Vacantes ordenadas por compatibilidad
El dashboard SHALL mostrar las vacantes analizadas de la persona que alcanzan el puntaje mínimo configurado en su perfil, ordenar Recomendaciones por puntaje decimal descendente y ordenar las demás etapas de seguimiento desde la entrada más reciente al estado hasta la más antigua. Las tarjetas SHALL mostrar solo estrellas y conservar el puntaje exacto en su etiqueta accesible.

#### Scenario: Hay varias vacantes analizadas
- **WHEN** la persona abre su dashboard y tiene varias vacantes analizadas que alcanzan el mínimo
- **THEN** Recomendaciones las muestra en orden descendente por el valor numérico completo del puntaje, incluidos los decimales

#### Scenario: Puntajes decimales y mínimo entero
- **WHEN** las vacantes tienen puntajes decimales y el perfil conserva un mínimo entero
- **THEN** la tarjeta muestra solo las estrellas y comunica el puntaje decimal exacto en su etiqueta accesible; Recomendaciones ordena por el valor decimal completo e incluye puntajes desde el mínimo entero correspondiente

#### Scenario: Vacante por debajo del mínimo del perfil
- **WHEN** una vacante tiene un puntaje inferior al mínimo configurado en el perfil
- **THEN** el sistema la excluye de Recomendaciones y conserva las vacantes que ya pertenecen a otros estados de seguimiento

#### Scenario: Puntaje mínimo igual a cero
- **WHEN** el perfil tiene un mínimo de 0
- **THEN** el sistema no excluye vacantes por su puntaje

#### Scenario: Vacantes en una pestaña de seguimiento
- **WHEN** la persona consulta aplicadas, en proceso, entrevista, finalizadas o descartadas
- **THEN** el sistema conserva todas las vacantes del estado elegido y las ordena de la entrada más reciente al estado a la más antigua

#### Scenario: Una vacante avanza de estado
- **WHEN** una vacante cambia de etapa de seguimiento
- **THEN** su posición en el nuevo listado usa la fecha en que entró a ese estado, no la fecha de entrada a una etapa anterior

#### Scenario: Vacantes sin puntaje
- **WHEN** la persona consulta «Por analizar»
- **THEN** el sistema no les atribuye un orden por puntaje que todavía no existe y conserva el orden actual de la cola
