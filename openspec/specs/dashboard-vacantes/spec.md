# Dashboard de vacantes Specification

## Purpose

Presenta a cada persona las vacantes más relevantes para su búsqueda en un dashboard privado, con información suficiente para decidir si desea continuar en la fuente original.

## Requirements

### Requirement: Vacantes ordenadas por compatibilidad
El dashboard SHALL mostrar las vacantes analizadas que permanecen en Recomendaciones según su estado de seguimiento, ordenar Recomendaciones por puntaje decimal descendente y ordenar las demás etapas de seguimiento desde la entrada más reciente al estado hasta la más antigua. Las tarjetas SHALL mostrar solo estrellas y conservar el puntaje exacto en su etiqueta accesible.

#### Scenario: Hay varias vacantes analizadas
- **WHEN** la persona abre su dashboard y tiene varias vacantes analizadas pendientes de decisión
- **THEN** Recomendaciones las muestra en orden descendente por el valor numérico completo del puntaje, incluidos los decimales

#### Scenario: Puntajes decimales y mínimo entero
- **WHEN** las vacantes tienen puntajes decimales y se comparan con el umbral guardado al descubrir cada una
- **THEN** la tarjeta muestra solo las estrellas y comunica el puntaje decimal exacto en su etiqueta accesible; una vacante queda en Recomendaciones si su puntaje es igual o superior a ese umbral

#### Scenario: Vacante por debajo del mínimo del perfil
- **WHEN** una vacante recién descubierta tiene un puntaje inferior al umbral guardado para ese descubrimiento
- **THEN** el sistema la muestra en Descartadas y no en Recomendaciones, y conserva las vacantes que ya pertenecen a otros estados de seguimiento

#### Scenario: Una vacante nueva queda por debajo del umbral
- **WHEN** una vacante descubierta para el perfil obtiene un puntaje inferior al umbral guardado para ese descubrimiento
- **THEN** el sistema la muestra en Descartadas y no en Recomendaciones

#### Scenario: Cambia el umbral del perfil
- **WHEN** la persona cambia el umbral después de que una vacante fue descubierta
- **THEN** el dashboard conserva el estado de seguimiento existente de esa vacante

#### Scenario: Puntaje mínimo igual a cero
- **WHEN** el umbral guardado al descubrirse una vacante es 0
- **THEN** el sistema no la descarta automáticamente por puntaje

#### Scenario: Umbral guardado igual a cero
- **WHEN** el perfil tiene un umbral de 0 al descubrirse una vacante
- **THEN** el sistema no la descarta por puntaje

#### Scenario: Vacantes en una pestaña de seguimiento
- **WHEN** la persona consulta aplicadas, en proceso, entrevista, finalizadas o descartadas
- **THEN** el sistema conserva todas las vacantes del estado elegido y las ordena de la entrada más reciente al estado a la más antigua

#### Scenario: Una vacante avanza de estado
- **WHEN** una vacante cambia de etapa de seguimiento
- **THEN** su posición en el nuevo listado usa la fecha en que entró a ese estado, no la fecha de entrada a una etapa anterior

#### Scenario: Vacantes sin puntaje
- **WHEN** la persona consulta «Por analizar»
- **THEN** el sistema no les atribuye un orden por puntaje que todavía no existe y conserva el orden actual de la cola

### Requirement: Mostrar datos concretos y palabras clave
El dashboard SHALL destacar el cargo y mostrar los datos estructurados disponibles y hasta cinco palabras clave concisas de la vacante, sin desplegar la descripción completa en la tarjeta.

#### Scenario: Vacante con condiciones conocidas
- **WHEN** una recomendación tiene ubicación, salario, modalidad o contrato extraídos
- **THEN** la tarjeta muestra esos datos con etiquetas claras y omite los campos vacíos

#### Scenario: Vacante con palabras clave organizadas
- **WHEN** el análisis contiene palabras clave y otras categorías organizadas
- **THEN** la tarjeta muestra las palabras clave y mantiene las razones y aspectos por revisar en una sección secundaria

### Requirement: Información organizada de cada vacante
El dashboard SHALL mostrar la información organizada por IA, el puntaje de compatibilidad, las razones de coincidencia, los requisitos que no coinciden o no están evidenciados y el enlace a la publicación original.

#### Scenario: Persona consulta una vacante
- **WHEN** la persona revisa una vacante del dashboard
- **THEN** ve la información organizada por IA y puede consultar la publicación en su fuente

### Requirement: Mostrar solo estrellas como puntaje visible en la tarjeta
El dashboard SHALL mostrar el puntaje de compatibilidad de cada tarjeta con estrellas y SHALL NOT mostrar junto a ellas la fracción numérica sobre 10, manteniendo el valor exacto en la etiqueta accesible.

#### Scenario: Persona consulta una recomendación
- **WHEN** una tarjeta muestra una vacante con puntaje calculado
- **THEN** se ven las estrellas sin una fracción como «7/10» debajo o al lado

#### Scenario: Se consulta con tecnología de asistencia
- **WHEN** una tecnología de asistencia lee el puntaje de una tarjeta
- **THEN** se anuncia el puntaje numérico exacto y su equivalencia visual en estrellas

#### Scenario: El puntaje se usa en filtros y orden
- **WHEN** el sistema filtra u ordena vacantes por compatibilidad
- **THEN** usa el puntaje numérico exacto sin depender de la presentación visual en estrellas

### Requirement: Enlace a la publicación original
El dashboard SHALL conservar un enlace a la publicación original para que la persona consulte los detalles en la fuente.

#### Scenario: Persona desea continuar con una vacante
- **WHEN** la persona selecciona el enlace de una vacante
- **THEN** el sistema abre la publicación original y la persona decide y realiza allí cualquier postulación

### Requirement: Filtrar vacantes por puntaje en el dashboard
El dashboard SHALL permitir filtrar temporalmente las recomendaciones por un puntaje mínimo entre 0 y 10, sin cambiar su estado de seguimiento ni aplicar retroactivamente el umbral de descarte del perfil.

#### Scenario: Se muestran todas las vacantes permitidas por el perfil
- **WHEN** la persona deja el filtro temporal en 0
- **THEN** el dashboard muestra todas las vacantes que permanecen en Recomendaciones

#### Scenario: La persona eleva el mínimo del listado
- **WHEN** la persona selecciona un puntaje mínimo mayor que 0
- **THEN** el dashboard muestra solo recomendaciones cuyo puntaje sea igual o superior al umbral temporal

#### Scenario: El umbral del listado está por debajo del perfil
- **WHEN** la persona selecciona un umbral temporal válido inferior al umbral de descarte guardado en el perfil
- **THEN** el dashboard usa ese valor únicamente para filtrar recomendaciones y no cambia el umbral de descarte ni los estados existentes

#### Scenario: Cambiar el filtro no modifica el perfil
- **WHEN** la persona cambia el umbral temporal del listado
- **THEN** el umbral de descarte guardado en el perfil permanece sin cambios

#### Scenario: Cambiar el filtro no modifica el perfil ni el seguimiento
- **WHEN** la persona cambia el umbral temporal del listado
- **THEN** el sistema conserva el umbral de descarte del perfil y los estados de seguimiento existentes

### Requirement: Ajustar el filtro temporal seleccionando estrellas
El dashboard SHALL permitir ajustar el filtro temporal del listado mediante opciones seleccionables representadas con estrellas, desde cero hasta cinco estrellas. Cada opción SHALL indicar de forma accesible que se muestran puntajes iguales o superiores al valor seleccionado y SHALL aplicarse al seleccionarla, sin botón de confirmación.

#### Scenario: Aplicar el filtro eligiendo estrellas
- **WHEN** la persona selecciona una opción de estrellas
- **THEN** el dashboard aplica el filtro de inmediato y muestra vacantes con puntaje igual o superior al mínimo elegido

#### Scenario: Mantener visible el mínimo del perfil
- **WHEN** la persona abre las recomendaciones sin haber seleccionado un filtro temporal
- **THEN** la opción seleccionada representa «Todas» y las opciones adicionales permiten filtrar por puntaje sin depender del umbral guardado en el perfil

#### Scenario: Abrir recomendaciones sin filtro temporal
- **WHEN** la persona abre las recomendaciones sin haber seleccionado un filtro temporal
- **THEN** el dashboard selecciona «Todas» y muestra las recomendaciones sin estrecharlas por puntaje

#### Scenario: Usar las opciones con teclado o lector de pantalla
- **WHEN** la persona recorre las opciones del filtro con teclado o lector de pantalla
- **THEN** cada opción comunica el umbral en estrellas y cuál está seleccionada

### Requirement: Conservar el filtro de puntaje al navegar el listado
El dashboard SHALL conservar el umbral temporal seleccionado al cambiar de página y al recargar el listado.

#### Scenario: Cambiar de página con un umbral activo
- **WHEN** la persona avanza o retrocede una página del listado filtrado
- **THEN** el listado conserva el mismo umbral temporal seleccionado

### Requirement: Validar el puntaje mínimo temporal
El dashboard SHALL aceptar únicamente umbrales temporales entre 0 y 10, independientes del umbral de descarte guardado en el perfil.

#### Scenario: Puntaje fuera del rango
- **WHEN** se solicita un umbral menor que 0, mayor que 10 o no numérico
- **THEN** el dashboard omite el filtro temporal y presenta todas las recomendaciones sin error

### Requirement: Consultar vacantes en espera de análisis
El dashboard SHALL ofrecer una vista privada de las vacantes cuyos análisis están pendientes para el perfil vigente de la persona.

#### Scenario: Hay análisis pendientes para el perfil vigente
- **WHEN** la persona abre la vista de vacantes por analizar
- **THEN** el sistema muestra las vacantes asociadas a análisis pendientes de su perfil y revisión vigente

#### Scenario: La persona consulta desde cuándo espera una vacante
- **WHEN** la vista muestra una vacante cuyo análisis está pendiente o en reintento
- **THEN** presenta la fecha y hora en que se creó el análisis vigente, que corresponde a su entrada a «Por analizar» y se conserva durante los reintentos

#### Scenario: La persona consulta el último intento de análisis
- **WHEN** existe al menos un intento de puntuación para la vacante pendiente
- **THEN** la tarjeta presenta la fecha y hora del intento más reciente de ese análisis y perfil

#### Scenario: El análisis pertenece a otra persona o revisión
- **WHEN** una vacante tiene un análisis pendiente para otro perfil o una revisión anterior
- **THEN** el sistema no la incluye en la vista del perfil actual

#### Scenario: No hay vacantes en espera de análisis
- **WHEN** la persona abre la vista y no tiene análisis pendientes vigentes
- **THEN** el sistema muestra un estado vacío que indica que no hay vacantes por analizar

### Requirement: Presentar los datos originales de vacantes pendientes
La vista de vacantes por analizar SHALL presentar los datos originales disponibles de la publicación sin atribuirle resultados generados por IA.

#### Scenario: Vacante pendiente con datos disponibles
- **WHEN** la vista muestra una vacante cuyo análisis sigue pendiente
- **THEN** presenta su cargo, empresa, ubicación, fuente, descripción original disponible y enlace a la publicación, y no muestra puntaje ni resumen generado por IA

#### Scenario: Vacante pendiente con datos incompletos
- **WHEN** la publicación no contiene alguno de los datos mostrables
- **THEN** la vista omite ese dato o lo marca como no informado sin inventarlo

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

### Requirement: Mostrar el conteo de vacantes por analizar
La pestaña «Por analizar» SHALL mostrar el conteo de vacantes únicas pendientes para el perfil y revisión vigentes.

#### Scenario: Hay vacantes pendientes
- **WHEN** existen vacantes pendientes de análisis para el perfil y revisión vigentes
- **THEN** el conteo de «Por analizar» coincide con el número de vacantes únicas que muestra la pestaña

#### Scenario: No hay vacantes pendientes
- **WHEN** no existen vacantes pendientes de análisis para el perfil y revisión vigentes
- **THEN** la pestaña muestra el conteo cero

### Requirement: Consultar vacantes por estado de seguimiento
El dashboard SHALL presentar como pestañas las recomendaciones pendientes de decisión y las vacantes aplicadas, en proceso, en entrevista, finalizadas y descartadas del perfil actual.

#### Scenario: La persona abre el dashboard de vacantes
- **WHEN** la persona consulta las recomendaciones sin elegir otro estado
- **THEN** el sistema muestra las vacantes pendientes de decisión

#### Scenario: La persona selecciona otra pestaña de seguimiento
- **WHEN** la persona selecciona aplicadas, en proceso, entrevista, finalizadas o descartadas
- **THEN** el sistema muestra solo las vacantes del perfil actual cuyo estado coincide con el filtro

#### Scenario: No hay vacantes en el estado elegido
- **WHEN** el perfil no tiene vacantes en el estado seleccionado
- **THEN** el sistema muestra un estado vacío para ese listado

#### Scenario: La persona descarta una vacante en seguimiento
- **WHEN** la persona descarta una vacante desde cualquier estado de seguimiento
- **THEN** deja de aparecer en el listado del estado anterior y aparece en el de descartadas

#### Scenario: La persona restaura una vacante descartada
- **WHEN** la persona restaura una vacante desde el listado de descartadas
- **THEN** deja de aparecer en descartadas y vuelve al listado del estado que tenía antes del descarte

### Requirement: Mantener vacantes descartadas fuera de Recomendaciones
El dashboard SHALL excluir de Recomendaciones y de su conteo las vacantes que el perfil actual haya descartado, aunque la vacante vuelva a ingerirse o tenga un análisis nuevo. El descarte SHALL permanecer vigente hasta que la persona restaure explícitamente la vacante.

#### Scenario: Se vuelve a analizar una vacante descartada
- **WHEN** una vacante descartada para el perfil actual recibe un análisis nuevo o actualizado
- **THEN** el dashboard la mantiene fuera de Recomendaciones y no cambia su seguimiento descartado

#### Scenario: Una búsqueda vuelve a encontrar la vacante descartada
- **WHEN** la ingesta encuentra nuevamente una vacante descartada para el perfil actual
- **THEN** la vacante no reaparece como recomendación y el conteo de Recomendaciones no aumenta por ella

#### Scenario: El seguimiento descartado está archivado
- **WHEN** una vacante descartada y archivada se ingiere o analiza de nuevo
- **THEN** el sistema no crea otro seguimiento pendiente y la mantiene fuera de Recomendaciones

#### Scenario: Otro perfil no descartó la vacante
- **WHEN** un perfil descartó una vacante compartida y otro perfil tiene un seguimiento no descartado para esa misma vacante
- **THEN** el dashboard del segundo perfil sigue mostrando la vacante según su propio estado y puntaje

#### Scenario: La persona restaura la vacante
- **WHEN** la persona restaura explícitamente una vacante descartada
- **THEN** el sistema recupera el estado previo al descarte y la muestra en el listado correspondiente

### Requirement: Mostrar conteos por pestaña de seguimiento
Cada pestaña de seguimiento SHALL mostrar el número de vacantes únicas visibles para el perfil actual en ese estado.

#### Scenario: El estado contiene vacantes
- **WHEN** una pestaña de seguimiento contiene vacantes del perfil actual
- **THEN** el conteo coincide con las vacantes únicas presentadas en esa pestaña

#### Scenario: La persona cambia el estado de una vacante
- **WHEN** una vacante se mueve a otro estado de seguimiento
- **THEN** se actualizan los conteos de las pestañas de origen y destino junto con sus listados

#### Scenario: El estado no contiene vacantes
- **WHEN** el perfil actual no tiene vacantes en un estado
- **THEN** la pestaña de ese estado muestra el conteo cero

#### Scenario: Una vacante cambia de etapa
- **WHEN** una vacante se descarta, se restaura o se avanza a otra etapa
- **THEN** cada conteo refleja las vacantes únicas visibles en su estado actual

### Requirement: Ocultar seguimientos archivados
El dashboard SHALL excluir de las pestañas y sus conteos los seguimientos archivados del perfil actual.

#### Scenario: El estado del perfil está archivado
- **WHEN** un seguimiento archivado pertenece al perfil actual
- **THEN** la vacante deja de aparecer en las recomendaciones o pestañas de seguimiento de ese perfil y no se incluye en sus conteos

#### Scenario: Otro perfil conserva la vacante activa
- **WHEN** el seguimiento de una vacante se archiva para un perfil pero sigue activo para otro
- **THEN** el dashboard del otro perfil conserva la vacante en su estado y conteo correspondientes

#### Scenario: El registro de vacante se conserva
- **WHEN** se oculta un seguimiento archivado
- **THEN** la vacante compartida y los datos de análisis permanecen almacenados

### Requirement: Ordenar las pestañas según el flujo de vacantes
El dashboard SHALL ordenar sus pestañas desde el análisis pendiente hasta las decisiones y avances de postulación.

#### Scenario: La persona consulta el dashboard de vacantes
- **WHEN** se muestran las pestañas del dashboard
- **THEN** aparecen en este orden: «Por analizar», «Recomendaciones», «Aplicadas», «En proceso», «Entrevista», «Finalizadas» y «Descartadas»

### Requirement: Mostrar antigüedad de publicación
El dashboard SHALL mostrar cuánto tiempo ha pasado desde la publicación de una vacante cuando la fuente proporciona esa fecha.

#### Scenario: La vacante tiene fecha de publicación
- **WHEN** una vacante visible tiene una fecha de publicación
- **THEN** el dashboard muestra una etiqueta relativa en español, como «Publicada hace 30 min» o «Publicada hace 2 horas»

#### Scenario: La vacante no tiene fecha de publicación
- **WHEN** una vacante visible no tiene fecha de publicación disponible
- **THEN** el dashboard omite la etiqueta de antigüedad sin inventar una fecha

### Requirement: Mostrar antigüedad del análisis
El dashboard SHALL mostrar cuánto tiempo ha pasado desde que se completó el análisis vigente de la vacante para el perfil actual.

#### Scenario: Vacante recomendada con análisis completado
- **WHEN** una vacante aparece en Recomendaciones con un análisis vigente completado
- **THEN** el dashboard muestra «Analizada hace…» usando la fecha de finalización de ese análisis para el perfil actual

#### Scenario: Vacante todavía sin análisis completado
- **WHEN** una vacante aún no tiene un análisis vigente completado para el perfil actual
- **THEN** el dashboard no muestra una etiqueta de análisis como si ya se hubiera completado

### Requirement: Mostrar antigüedad del estado actual
El dashboard SHALL mostrar cuánto tiempo lleva una vacante en el estado de seguimiento actual del perfil.

#### Scenario: Vacante en una etapa de postulación
- **WHEN** una vacante se muestra como aplicada, en proceso, en entrevista, finalizada o descartada
- **THEN** el dashboard muestra una etiqueta como «Aplicada hace…» o «Entrevista hace…» basada en la fecha en que entró a ese estado

#### Scenario: Vacante en Recomendaciones
- **WHEN** una vacante aparece en Recomendaciones sin haber avanzado a otro estado
- **THEN** el dashboard usa la fecha de finalización del análisis vigente para indicar «Analizada hace…»

#### Scenario: La vacante cambia de estado
- **WHEN** una vacante pasa a un estado distinto
- **THEN** la antigüedad del nuevo estado comienza desde ese cambio y no reutiliza la duración del estado anterior

#### Scenario: Mostrar tiempos relativos
- **WHEN** el dashboard muestra una fecha de publicación, análisis o estado
- **THEN** expresa el tiempo transcurrido con unidades legibles en español y conserva la fecha y hora exactas en un formato accesible

### Requirement: Reflejar el descarte automático de recomendaciones
El dashboard SHALL mostrar en Descartadas las recomendaciones vencidas que el proceso automático cambie de estado para el perfil actual.

#### Scenario: La tarea descarta una recomendación vencida
- **WHEN** una recomendación del perfil actual cumple siete días y la tarea diaria la descarta
- **THEN** deja de aparecer en Recomendaciones, aparece en Descartadas y se actualizan los conteos de ambas pestañas

#### Scenario: La persona restaura una recomendación vencida
- **WHEN** la persona restaura desde Descartadas una vacante descartada automáticamente
- **THEN** vuelve a aparecer en Recomendaciones y su conteo refleja el cambio

### Requirement: Saltar directamente a una página del listado
El dashboard SHALL mostrar números de página en los listados de vacantes paginados y permitir navegar directamente a la página seleccionada, conservando la pestaña y los filtros activos.

#### Scenario: La persona selecciona un número de página
- **WHEN** la persona elige un número distinto de la página actual
- **THEN** el listado muestra las vacantes de la página elegida sin navegar página por página

#### Scenario: Se conserva el estado y los filtros
- **WHEN** la persona salta a otra página con una pestaña de seguimiento o filtro de puntaje activo
- **THEN** el listado mantiene la pestaña y los filtros seleccionados

#### Scenario: La página actual está identificada
- **WHEN** se presenta la navegación numerada
- **THEN** el número de la página actual se distingue visualmente y se identifica como actual para tecnologías de asistencia

#### Scenario: El listado tiene muchas páginas
- **WHEN** el total de páginas es demasiado amplio para mostrar todos los números de forma legible
- **THEN** la navegación muestra un conjunto compacto que incluye páginas cercanas a la actual, acceso a la primera y última página, y una indicación de los intervalos omitidos

#### Scenario: El listado cabe en una sola página
- **WHEN** el total de resultados ocupa una sola página
- **THEN** el listado no muestra controles de paginación innecesarios

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
- **WHEN** la persona elige usar una recomendación de puntaje
- **THEN** el sistema abre Recomendaciones con ese valor entero aplicado al filtro temporal sin modificar el perfil ni el estado de las vacantes

#### Scenario: La recomendación está por debajo del mínimo guardado
- **WHEN** la mediana recomendada es inferior al umbral actual de descarte del perfil
- **THEN** la pantalla «Análisis» permite aplicarla como filtro temporal y explica que esto no cambia el umbral ni modifica estados existentes

#### Scenario: La persona no aplica la recomendación
- **WHEN** la persona consulta una recomendación sin seleccionarla
- **THEN** el filtro temporal y el mínimo guardado permanecen sin cambios
