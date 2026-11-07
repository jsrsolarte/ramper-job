# Presentación de vacantes Specification

## Purpose

Organiza la información obtenida de las vacantes para que sea breve, verificable y útil al comparar oportunidades.

## Requirements

### Requirement: Organizar la información de la vacante
El sistema SHALL conservar una síntesis y categorías organizadas de la publicación, omitiendo secciones sin información respaldada y permitiendo que este contenido esté disponible después del puntaje de compatibilidad.

#### Scenario: Publicación con información suficiente
- **WHEN** la IA organiza una vacante con información sobre el cargo
- **THEN** el resultado conserva el resumen, las palabras clave y las categorías identificables de responsabilidades, requisitos y condiciones

#### Scenario: Publicación con información incompleta
- **WHEN** la publicación no especifica una de las secciones
- **THEN** el sistema omite esa sección sin completarla por inferencia

#### Scenario: Puntaje disponible y organización pendiente
- **WHEN** una vacante ya tiene puntaje y su organización está pendiente
- **THEN** el dashboard muestra el puntaje y señala que el contenido organizado está pendiente

#### Scenario: Mínimo reducido y organización pendiente
- **WHEN** una reducción del mínimo hace visible una vacante cuyo puntaje ya estaba guardado y la organización acaba de encolarse
- **THEN** el dashboard muestra el puntaje y señala que el contenido organizado está pendiente

#### Scenario: Puntaje disponible y organización fallida
- **WHEN** la organización no se puede completar después de los reintentos disponibles
- **THEN** el dashboard conserva la vacante y el puntaje e indica que el contenido organizado no está disponible

### Requirement: Limitar la síntesis a información verificable
El sistema SHALL basar el contenido organizado solo en la publicación y conservar su URL original para consultar detalles directamente en la fuente.

#### Scenario: Resumen sin invenciones
- **WHEN** la IA organiza el texto de una vacante
- **THEN** la síntesis usa información presente en la publicación y conserva el enlace original

### Requirement: Presentar palabras clave de forma concisa
El dashboard SHALL mostrar las palabras clave de la descripción sin presentar la descripción completa en la tarjeta.

#### Scenario: Categorías adicionales disponibles
- **WHEN** se guardan responsabilidades, requisitos o condiciones organizadas por IA
- **THEN** el sistema conserva esas categorías en la base de datos y presenta las palabras clave de manera concisa en la tarjeta

### Requirement: Solicitar una organización enfocada en lo esencial
El sistema SHALL solicitar que la organización de la vacante incluya solo información principal y útil para compararla, omitiendo detalles secundarios o redundantes sin imponer un límite de longitud ni eliminar categorías respaldadas por la publicación.

#### Scenario: Publicación con información repetida
- **WHEN** la publicación repite una responsabilidad, requisito o condición con otras palabras
- **THEN** la organización expresa el contenido una sola vez y conserva la idea principal

#### Scenario: Publicación con varias responsabilidades o requisitos distintos
- **WHEN** la vacante contiene varios elementos distintos que afectan su comparación
- **THEN** la organización conserva esos elementos y omite explicaciones auxiliares que no agregan información

#### Scenario: Publicación con datos insuficientes
- **WHEN** la publicación no permite identificar información principal de una categoría
- **THEN** la respuesta omite esa categoría sin inferir ni completar detalles

#### Scenario: Se verifica el consumo de salida
- **WHEN** se compara la nueva instrucción con la versión anterior usando publicaciones representativas
- **THEN** la respuesta conserva la información estructurada necesaria y reduce el consumo medio de tokens de salida
