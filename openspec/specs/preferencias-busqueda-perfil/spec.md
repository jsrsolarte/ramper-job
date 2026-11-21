# Preferencias de búsqueda del perfil Specification

## Purpose

Permite a cada aspirante expresar preferencias concretas y combinarlas con sugerencias respaldadas por su hoja de vida para encontrar vacantes relevantes.

## Requirements

### Requirement: Administrar frases de búsqueda
El sistema SHALL permitir que cada aspirante agregue y quite frases independientes que describan cargos, áreas o condiciones de búsqueda.

#### Scenario: Agregar frases al perfil
- **WHEN** el aspirante guarda una o más frases válidas
- **THEN** el sistema conserva cada frase por separado en la revisión vigente

#### Scenario: Quitar una frase
- **WHEN** el aspirante elimina una frase y guarda el perfil
- **THEN** las próximas búsquedas usan las frases restantes y la nueva revisión no conserva la frase eliminada

### Requirement: Definir ubicaciones y trabajo remoto
El sistema SHALL permitir registrar varias ubicaciones de interés y si el aspirante acepta vacantes remotas.

#### Scenario: Buscar en varias ubicaciones
- **WHEN** el perfil incluye varias ubicaciones
- **THEN** el sistema las considera en las búsquedas y el análisis de compatibilidad

#### Scenario: Aceptar trabajo remoto
- **WHEN** el aspirante activa la preferencia de trabajo remoto
- **THEN** el análisis puede considerar una vacante explícitamente remota como compatible con la ubicación

#### Scenario: No aceptar trabajo remoto
- **WHEN** el aspirante no acepta trabajo remoto y la vacante no coincide con sus ubicaciones
- **THEN** el sistema no crea un análisis para esa combinación ni presenta la vacante como recomendación

### Requirement: Complementar frases con la hoja de vida
El sistema SHALL permitir que la IA añada términos de búsqueda respaldados por el contenido del CV sin sustituir las frases elegidas por el aspirante.

#### Scenario: Generar términos complementarios
- **WHEN** el sistema prepara la búsqueda para una revisión de perfil
- **THEN** la IA conserva las frases del aspirante y puede añadir términos concretos sustentados por su CV

#### Scenario: El CV no respalda términos adicionales
- **WHEN** el CV no respalda términos adicionales útiles
- **THEN** el sistema busca con las frases del aspirante sin inventar cargos ni experiencia

### Requirement: Descargar la hoja de vida de forma privada
El sistema SHALL servir la hoja de vida únicamente a su propietario autenticado mediante una ruta asociada a su perfil.

#### Scenario: El propietario descarga su hoja de vida
- **WHEN** el aspirante autenticado solicita la descarga de su archivo vigente
- **THEN** el sistema devuelve el archivo del perfil

#### Scenario: Otra cuenta intenta acceder al archivo
- **WHEN** una cuenta distinta o una persona no autenticada solicita el archivo privado
- **THEN** el sistema no revela ni entrega el archivo

### Requirement: Definir un puntaje mínimo por perfil
El sistema SHALL permitir que cada aspirante seleccione y guarde un puntaje entero entre 0 y 5 como umbral de descarte automático para vacantes descubiertas en adelante.

#### Scenario: Guardar el puntaje mínimo
- **WHEN** el aspirante selecciona un valor entre 0 y 5 y guarda el perfil
- **THEN** el sistema conserva ese umbral para aplicarlo a vacantes que se descubran posteriormente para ese perfil

#### Scenario: Perfil sin umbral configurado
- **WHEN** un perfil todavía no tiene un umbral guardado
- **THEN** el sistema aplica 0 y no descarta vacantes por puntaje

#### Scenario: Perfil sin descarte por puntaje
- **WHEN** el perfil tiene un umbral de 0
- **THEN** el sistema no descarta vacantes por puntaje

#### Scenario: Valor fuera de rango
- **WHEN** se intenta guardar un valor menor que 0, mayor que 5 o no entero
- **THEN** el sistema rechaza el valor e informa que el umbral debe ser un entero de 0 a 5

#### Scenario: El análisis nuevo queda por debajo del umbral
- **WHEN** se completa el análisis de una vacante descubierta después de guardar el umbral y su puntaje es menor que el valor guardado al descubrirla
- **THEN** el seguimiento de esa vacante se marca como descartado automáticamente

#### Scenario: El puntaje alcanza el umbral
- **WHEN** el análisis de una nueva vacante obtiene un puntaje igual o superior al umbral guardado al descubrirla
- **THEN** el sistema conserva la vacante como recomendación pendiente de decisión

### Requirement: Cambiar el umbral sin reanalizar vacantes
El sistema SHALL aplicar el puntaje guardado al descubrir una vacante para el perfil y SHALL NOT volver a evaluar vacantes ya descubiertas únicamente porque cambie ese valor.

#### Scenario: Aspirante ajusta el mínimo
- **WHEN** el aspirante cambia y guarda el puntaje mínimo
- **THEN** el sistema lo conserva para vacantes descubiertas posteriormente, no encola análisis ni modifica puntajes, análisis o estados de seguimiento existentes

#### Scenario: La vacante ya estaba descartada
- **WHEN** el aspirante cambia el umbral después de que una vacante fue descartada
- **THEN** la vacante permanece descartada y no se reactiva automáticamente

### Requirement: Seleccionar el puntaje mínimo con estrellas
Mi perfil SHALL permitir seleccionar el umbral de descarte automático con opciones representadas únicamente por estrellas visuales, con las seis opciones enteras 0, 1, 2, 3, 4 y 5, incluida la opción visual de cero estrellas, y comunicar mediante accesibilidad que los puntajes inferiores se descartan automáticamente para vacantes nuevas.

#### Scenario: Cambiar el mínimo guardado
- **WHEN** la persona selecciona una opción de estrellas y guarda el perfil
- **THEN** el sistema guarda el umbral y explica que los puntajes inferiores moverán las nuevas vacantes a Descartadas

#### Scenario: Elegir cero como mínimo
- **WHEN** la persona elige la opción de cero estrellas y guarda el perfil
- **THEN** el perfil no descarta vacantes por puntaje

#### Scenario: Usar las opciones con teclado o lector de pantalla
- **WHEN** la persona recorre las opciones con teclado o lector de pantalla
- **THEN** cada opción comunica el umbral en estrellas y cuál está seleccionada

#### Scenario: Guardar una nueva preferencia
- **WHEN** la persona guarda el formulario con un mínimo distinto
- **THEN** el sistema aplica el nuevo umbral solo a vacantes descubiertas posteriormente, sin reanalizar ni cambiar los estados de vacantes ya descubiertas

#### Scenario: Cambiar un umbral con vacantes existentes
- **WHEN** la persona guarda un umbral distinto
- **THEN** el sistema no cambia los estados existentes y no reactiva vacantes descartadas

### Requirement: Pausar o reanudar la búsqueda automática del perfil
«Mi perfil» SHALL permitir a la persona propietaria pausar o reanudar las búsquedas automáticas de su perfil, sin desactivar su cuenta ni modificar sus demás datos.

#### Scenario: Perfil nuevo o existente sin configuración de búsqueda
- **WHEN** el sistema crea un perfil o encuentra uno que todavía no tiene un estado de búsqueda guardado
- **THEN** considera habilitada la búsqueda automática para conservar el comportamiento vigente

#### Scenario: La persona pausa la búsqueda de su perfil
- **WHEN** la persona desactiva el control de búsqueda en «Mi perfil» y guarda el cambio
- **THEN** el sistema conserva esa preferencia, muestra que la búsqueda está pausada y mantiene disponibles la cuenta, el CV, las preferencias y los resultados guardados

#### Scenario: La persona reanuda la búsqueda de su perfil
- **WHEN** la persona activa el control de búsqueda en «Mi perfil» y guarda el cambio
- **THEN** el sistema conserva la preferencia habilitada y comunica que el perfil volverá a participar en las siguientes búsquedas automáticas

#### Scenario: Cambiar solo el estado de búsqueda
- **WHEN** la persona cambia el control de búsqueda sin modificar otros datos del perfil
- **THEN** el sistema no crea una nueva revisión del CV o de preferencias ni encola una búsqueda inmediata

### Requirement: Convertir los umbrales históricos del perfil
El sistema SHALL convertir los mínimos históricos a estrellas y redondear hacia el entero superior, sin cambiar los estados existentes.

#### Scenario: Mínimo histórico de media estrella
- **WHEN** un perfil tiene un mínimo antiguo equivalente a 2,5 estrellas
- **THEN** su nuevo mínimo es 3 estrellas y se aplica solo a las vacantes descubiertas en adelante

#### Scenario: Reintentar la migración
- **WHEN** se repite la conversión
- **THEN** no se convierte otra vez el umbral ya migrado ni se reevalúan vacantes existentes
