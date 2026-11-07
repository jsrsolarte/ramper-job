# Spec Delta

## ADDED Requirements

### Requirement: Ver la distribución de puntajes del perfil
El dashboard SHALL mostrar la distribución de los puntajes vigentes del perfil, incluidos los resultados inferiores al mínimo que actualmente los oculta.

#### Scenario: Hay análisis vigentes con distintos puntajes
- **WHEN** la persona consulta la distribución
- **THEN** el dashboard muestra conteos por intervalos enteros de puntaje entre 0 y 10, calculados con análisis completados de la revisión y rúbrica vigentes

#### Scenario: Hay resultados por debajo del mínimo
- **WHEN** algunos análisis vigentes no aparecen en la lista por el umbral actual
- **THEN** esos análisis también cuentan en la distribución

#### Scenario: No hay análisis vigentes
- **WHEN** el perfil aún no tiene análisis completados de la revisión y rúbrica vigentes
- **THEN** el dashboard indica que aún no hay datos suficientes para mostrar la distribución

#### Scenario: La distribución no desplaza las vacantes del foco principal
- **WHEN** la persona consulta Recomendaciones
- **THEN** el dashboard muestra primero el filtro y el listado de vacantes, y presenta la distribución debajo del listado y su paginación

### Requirement: Recomendar un puntaje mínimo a partir de la distribución
El dashboard SHALL recomendar un umbral entero entre 0 y 10 usando la mediana de los puntajes vigentes y explicar la recomendación.

#### Scenario: Hay al menos cinco análisis vigentes
- **WHEN** la persona consulta la distribución con cinco o más análisis completados vigentes
- **THEN** el sistema recomienda la mediana redondeada al entero más cercano, redondeando los empates de 0.5 hacia arriba, e indica el tamaño de la muestra y cuántos análisis quedarían en o por encima del umbral

#### Scenario: Hay menos de cinco análisis vigentes
- **WHEN** el perfil tiene menos de cinco análisis completados vigentes
- **THEN** el dashboard informa que necesita más resultados y no presenta un umbral recomendado

### Requirement: Aplicar la recomendación solo por decisión de la persona
El dashboard SHALL mantener los filtros como enteros de 0 a 10 y SHALL NOT cambiar el filtro ni la preferencia guardada del perfil sin una acción expresa de la persona.

#### Scenario: La recomendación puede aplicarse al filtro temporal
- **WHEN** la persona elige usar una recomendación que no está por debajo del mínimo guardado en el perfil
- **THEN** el sistema aplica el valor entero al filtro temporal del listado sin modificar el perfil

#### Scenario: La recomendación está por debajo del mínimo guardado
- **WHEN** la mediana recomendada es inferior al mínimo guardado en el perfil
- **THEN** el dashboard explica que el mínimo del perfil sigue limitando el listado y ofrece ir a la configuración del perfil para cambiarlo

#### Scenario: La persona no aplica la recomendación
- **WHEN** la persona consulta una recomendación sin seleccionarla
- **THEN** el filtro temporal y el mínimo guardado permanecen sin cambios
