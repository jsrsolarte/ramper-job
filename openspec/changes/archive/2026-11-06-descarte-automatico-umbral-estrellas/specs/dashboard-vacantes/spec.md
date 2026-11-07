# Spec Delta

## MODIFIED Requirements

### Requirement: Vacantes ordenadas por compatibilidad
El dashboard SHALL mostrar las vacantes analizadas que permanecen en Recomendaciones según su estado de seguimiento, ordenar Recomendaciones por puntaje decimal descendente y ordenar las demás etapas de seguimiento desde la entrada más reciente al estado hasta la más antigua. Las tarjetas SHALL mostrar solo estrellas y conservar el puntaje exacto en su etiqueta accesible.

#### Scenario: Hay varias vacantes analizadas
- **WHEN** la persona abre su dashboard y tiene varias vacantes analizadas pendientes de decisión
- **THEN** Recomendaciones las muestra en orden descendente por el valor numérico completo del puntaje, incluidos los decimales

#### Scenario: Puntajes decimales y mínimo entero
- **WHEN** las vacantes tienen puntajes decimales y se comparan con el umbral guardado al descubrir cada una
- **THEN** la tarjeta muestra solo las estrellas y comunica el puntaje decimal exacto en su etiqueta accesible; una vacante queda en Recomendaciones si su puntaje es igual o superior a ese umbral

#### Scenario: Vacante por debajo del mínimo del perfil
- **WHEN** una vacante descubierta para el perfil obtiene un puntaje inferior al umbral guardado para ese descubrimiento
- **THEN** el sistema la muestra en Descartadas y no en Recomendaciones

#### Scenario: Cambia el umbral del perfil
- **WHEN** la persona cambia el umbral después de que una vacante fue descubierta
- **THEN** el dashboard conserva el estado de seguimiento existente de esa vacante

#### Scenario: Umbral guardado igual a cero
- **WHEN** el perfil tiene un umbral de 0 al descubrirse una vacante
- **THEN** el sistema no la descarta por puntaje

#### Scenario: Puntaje mínimo igual a cero
- **WHEN** el perfil tenía un mínimo de 0 cuando se descubrió la vacante
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

### Requirement: Filtrar vacantes por puntaje en el dashboard
El dashboard SHALL permitir filtrar temporalmente las recomendaciones por un puntaje mínimo entre 0 y 10, sin cambiar su estado de seguimiento ni aplicar retroactivamente el umbral de descarte del perfil.

#### Scenario: Se muestran todas las vacantes permitidas por el perfil
- **WHEN** la persona deja el filtro temporal en 0
- **THEN** el dashboard muestra todas las vacantes que permanecen en Recomendaciones

#### Scenario: La persona eleva el mínimo del listado
- **WHEN** la persona selecciona un puntaje mínimo mayor que 0
- **THEN** el dashboard muestra solo recomendaciones cuyo puntaje sea igual o superior al umbral temporal

#### Scenario: Cambiar el filtro no modifica el perfil ni el seguimiento
- **WHEN** la persona cambia el umbral temporal del listado
- **THEN** el sistema conserva el umbral de descarte del perfil y los estados de seguimiento existentes

#### Scenario: El umbral del listado está por debajo del perfil
- **WHEN** la persona selecciona un umbral temporal válido inferior al umbral de descarte del perfil
- **THEN** el dashboard lo usa solo para filtrar recomendaciones y no cambia el umbral del perfil ni los estados existentes

#### Scenario: Cambiar el filtro no modifica el perfil
- **WHEN** la persona cambia el umbral temporal del listado
- **THEN** el umbral de descarte guardado en el perfil permanece sin cambios

### Requirement: Ajustar el filtro temporal seleccionando estrellas
El dashboard SHALL permitir ajustar el filtro temporal del listado mediante opciones seleccionables representadas con estrellas, desde cero hasta cinco estrellas. Cada opción SHALL indicar de forma accesible que se muestran puntajes iguales o superiores al valor seleccionado y SHALL aplicarse al seleccionarla, sin botón de confirmación.

#### Scenario: Aplicar el filtro eligiendo estrellas
- **WHEN** la persona selecciona una opción de estrellas
- **THEN** el dashboard aplica el filtro de inmediato y muestra recomendaciones con puntaje igual o superior al mínimo elegido

#### Scenario: Mantener visible el mínimo del perfil
- **WHEN** la persona abre las recomendaciones sin haber seleccionado un filtro temporal
- **THEN** el dashboard selecciona «Todas» y muestra las recomendaciones sin estrecharlas por puntaje

#### Scenario: Usar las opciones con teclado o lector de pantalla
- **WHEN** la persona recorre las opciones del filtro con teclado o lector de pantalla
- **THEN** cada opción comunica el umbral en estrellas y cuál está seleccionada

### Requirement: Validar el puntaje mínimo temporal
El dashboard SHALL aceptar únicamente umbrales temporales entre 0 y 10, independientes del umbral de descarte guardado en el perfil.

#### Scenario: Puntaje fuera del rango
- **WHEN** se solicita un umbral menor que 0, mayor que 10 o no numérico
- **THEN** el dashboard omite el filtro temporal y presenta todas las recomendaciones sin error

### Requirement: Aplicar la recomendación solo por decisión de la persona
El dashboard SHALL mantener los filtros como enteros de 0 a 10 y permitir usar desde la pantalla «Análisis» la recomendación como filtro temporal de Recomendaciones. SHALL NOT cambiar el filtro temporal, los estados de seguimiento ni el umbral de descarte del perfil sin una acción expresa de la persona.

#### Scenario: La recomendación puede aplicarse al filtro temporal
- **WHEN** la persona elige usar una recomendación de puntaje
- **THEN** el sistema abre Recomendaciones con ese valor entero aplicado al filtro temporal sin modificar el perfil ni el estado de las vacantes

#### Scenario: La recomendación está por debajo del mínimo guardado
- **WHEN** la mediana recomendada es inferior al umbral actual de descarte del perfil
- **THEN** la pantalla «Análisis» permite aplicarla como filtro temporal y explica que esto no cambia el umbral ni modifica estados existentes

#### Scenario: La persona no aplica la recomendación
- **WHEN** la persona consulta una recomendación sin seleccionarla
- **THEN** el filtro temporal, el umbral de descarte guardado y los estados de seguimiento permanecen sin cambios
