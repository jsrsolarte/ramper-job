# Spec Delta

## MODIFIED Requirements

### Requirement: Filtrar vacantes por puntaje en el dashboard
El dashboard SHALL permitir filtrar temporalmente cada estado de vacantes analizadas por una puntuación exacta entre 0 y 5 en incrementos de 0,5, sin cambiar su estado de seguimiento ni aplicar retroactivamente el umbral de descarte del perfil.

#### Scenario: Se muestran todas las vacantes permitidas por el perfil
- **WHEN** la persona deja el filtro temporal en «Todas»
- **THEN** el dashboard muestra todas las vacantes que permanecen en Recomendaciones

#### Scenario: La persona eleva el mínimo del listado
- **WHEN** la persona selecciona un puntaje mínimo mayor que 0
- **THEN** el dashboard muestra solo vacantes del estado actual cuya puntuación sea exactamente la seleccionada

#### Scenario: El umbral del listado está por debajo del perfil
- **WHEN** la persona selecciona una puntuación exacta inferior al umbral de descarte guardado en el perfil
- **THEN** el dashboard usa ese valor únicamente para filtrar el estado actual y no cambia el umbral de descarte ni los estados existentes

#### Scenario: Cambiar el filtro no modifica el perfil
- **WHEN** la persona cambia el umbral temporal del listado
- **THEN** el umbral de descarte guardado en el perfil permanece sin cambios

#### Scenario: Cambiar el filtro no modifica el perfil ni el seguimiento
- **WHEN** la persona cambia el umbral temporal del listado
- **THEN** el sistema conserva el umbral de descarte del perfil y los estados de seguimiento existentes

### Requirement: Ajustar el filtro temporal seleccionando estrellas
El dashboard SHALL representar visualmente con estrellas las puntuaciones del listado, filtros y distribución, incluso cero y medios puntos, en lugar de mostrar su valor como texto visible. SHALL conservar etiquetas accesibles con el valor exacto. El dashboard SHALL permitir ajustar el filtro temporal del listado mediante opciones seleccionables representadas con estrellas, solo para puntuaciones exactas disponibles en el estado actual, desde cero hasta cinco estrellas en medios puntos. Cada opción SHALL indicar de forma accesible que se muestran puntajes iguales al valor seleccionado y SHALL aplicarse al seleccionarla, sin botón de confirmación.

#### Scenario: Aplicar el filtro eligiendo estrellas
- **WHEN** la persona selecciona una opción de estrellas
- **THEN** el dashboard aplica el filtro de inmediato y muestra vacantes con puntaje exactamente igual al valor elegido

#### Scenario: Mantener visible el mínimo del perfil
- **WHEN** la persona abre las recomendaciones sin haber seleccionado un filtro temporal
- **THEN** la opción seleccionada representa «Todas» y las opciones adicionales permiten filtrar por puntaje sin depender del umbral guardado en el perfil

#### Scenario: Abrir recomendaciones sin filtro temporal
- **WHEN** la persona abre las recomendaciones sin haber seleccionado un filtro temporal
- **THEN** el dashboard selecciona «Todas» y muestra las recomendaciones sin estrecharlas por puntaje

#### Scenario: Usar las opciones con teclado o lector de pantalla
- **WHEN** la persona recorre las opciones del filtro con teclado o lector de pantalla
- **THEN** cada opción comunica la puntuación exacta en estrellas y cuál está seleccionada

### Requirement: Conservar el filtro de puntaje al navegar el listado
El dashboard SHALL conservar el filtro de puntuación exacta seleccionado al cambiar de página y al recargar el listado.

#### Scenario: Cambiar de página con un umbral activo
- **WHEN** la persona avanza o retrocede una página del listado filtrado
- **THEN** el listado conserva el mismo filtro de puntuación exacta seleccionado

### Requirement: Validar el puntaje mínimo temporal
El dashboard SHALL aceptar solo puntuaciones exactas disponibles de 0 a 5 en medios puntos, independientes del umbral de descarte guardado en el perfil.

#### Scenario: Puntaje fuera del rango
- **WHEN** se solicita una puntuación fuera de rango, que no sea múltiplo de 0,5 o no esté disponible en el estado
- **THEN** el dashboard omite el filtro temporal y presenta todas las vacantes del estado sin error

### Requirement: Limitar filtros a puntuaciones presentes por estado
Cada estado con vacantes analizadas SHALL ofrecer solo puntuaciones exactas existentes en ese estado y una opción «Todas», calculadas sobre todos sus resultados antes de paginar.

#### Scenario: Solo hay puntuaciones desde tres estrellas
- **WHEN** un estado contiene solo vacantes con 3, 3,5 y 5 estrellas
- **THEN** ofrece «Todas», 3, 3,5 y 5, sin ofrecer puntuaciones ausentes

#### Scenario: Se consulta otro estado
- **WHEN** la persona abre Descartadas u otro estado con puntuaciones distintas
- **THEN** las opciones reflejan las puntuaciones de ese estado, no las de Recomendaciones

#### Scenario: No hay resultados analizados
- **WHEN** el estado no contiene puntuaciones válidas
- **THEN** se conserva «Todas» y no se presentan opciones de puntuación inexistentes

#### Scenario: Cambia el conjunto de resultados
- **WHEN** deja de existir la puntuación seleccionada en el estado
- **THEN** el filtro vuelve a «Todas» sin cambiar estados ni preferencias
