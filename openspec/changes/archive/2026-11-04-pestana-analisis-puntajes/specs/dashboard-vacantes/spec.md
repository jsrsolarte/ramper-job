# Spec Delta

## MODIFIED Requirements

### Requirement: Ver la distribución de puntajes del perfil
El dashboard SHALL mostrar la distribución de los puntajes vigentes del perfil en una pantalla privada «Análisis», accesible desde la navegación principal junto a Mi perfil.

#### Scenario: Hay análisis vigentes con distintos puntajes
- **WHEN** la persona consulta la pantalla «Análisis»
- **THEN** el dashboard muestra conteos por intervalos enteros de puntaje entre 0 y 10, calculados con análisis completados de la revisión y rúbrica vigentes

#### Scenario: Hay resultados por debajo del mínimo
- **WHEN** algunos análisis vigentes no aparecen en la lista por el umbral actual
- **THEN** esos análisis también cuentan en la distribución

#### Scenario: No hay análisis vigentes
- **WHEN** el perfil aún no tiene análisis completados de la revisión y rúbrica vigentes
- **THEN** la pantalla «Análisis» indica que aún no hay datos suficientes para mostrar la distribución

#### Scenario: La distribución no desplaza las vacantes del foco principal
- **WHEN** la persona consulta Recomendaciones
- **THEN** el dashboard muestra primero el filtro y el listado de vacantes, y presenta la distribución debajo del listado y su paginación

#### Scenario: Recomendaciones mantiene el foco en las vacantes
- **WHEN** la persona consulta la pestaña «Recomendaciones»
- **THEN** el dashboard no muestra allí la distribución ni la sugerencia de puntaje

### Requirement: Navegar entre vacantes recomendadas y pendientes de análisis
El dashboard SHALL presentar las vacantes por analizar y las recomendaciones como pestañas de la experiencia privada de vacantes, y ofrecer «Análisis» como una pantalla independiente desde la navegación principal.

#### Scenario: La persona abre la pestaña de análisis pendiente
- **WHEN** la persona selecciona la pestaña «Por analizar»
- **THEN** el sistema muestra las vacantes pendientes del perfil actual sin cambiar el estado técnico de ningún análisis

#### Scenario: La persona abre las recomendaciones
- **WHEN** la persona selecciona la pestaña «Recomendaciones»
- **THEN** el sistema muestra las recomendaciones disponibles del perfil actual sin alterar los análisis pendientes

#### Scenario: La persona abre Análisis desde la navegación principal
- **WHEN** la persona selecciona «Análisis» junto a «Mi perfil»
- **THEN** el sistema muestra las métricas de puntaje de su perfil sin alterar análisis ni estados de seguimiento

### Requirement: Recomendar un puntaje mínimo a partir de la distribución
El dashboard SHALL recomendar en la pantalla «Análisis» un umbral entero entre 0 y 10 usando la mediana de los puntajes vigentes y explicar la recomendación.

#### Scenario: Hay al menos cinco análisis vigentes
- **WHEN** la persona consulta la distribución con cinco o más análisis completados vigentes
- **THEN** el sistema recomienda la mediana redondeada al entero más cercano, redondeando los empates de 0.5 hacia arriba, e indica el tamaño de la muestra y cuántos análisis quedarían en o por encima del umbral

#### Scenario: Hay menos de cinco análisis vigentes
- **WHEN** el perfil tiene menos de cinco análisis completados vigentes
- **THEN** la pantalla «Análisis» informa que necesita más resultados y no presenta un umbral recomendado

### Requirement: Aplicar la recomendación solo por decisión de la persona
El dashboard SHALL mantener los filtros como enteros de 0 a 10 y permitir usar desde la pantalla «Análisis» la recomendación como filtro temporal de Recomendaciones. SHALL NOT cambiar el filtro ni la preferencia guardada del perfil sin una acción expresa de la persona.

#### Scenario: La recomendación puede aplicarse al filtro temporal
- **WHEN** la persona elige usar una recomendación que no está por debajo del mínimo guardado en el perfil
- **THEN** el sistema abre Recomendaciones con el valor entero aplicado al filtro temporal sin modificar el perfil

#### Scenario: La recomendación está por debajo del mínimo guardado
- **WHEN** la mediana recomendada es inferior al mínimo guardado en el perfil
- **THEN** la pantalla «Análisis» explica que el mínimo del perfil sigue limitando el listado y ofrece ir a la configuración del perfil para cambiarlo

#### Scenario: La persona no aplica la recomendación
- **WHEN** la persona consulta una recomendación sin seleccionarla
- **THEN** el filtro temporal y el mínimo guardado permanecen sin cambios
