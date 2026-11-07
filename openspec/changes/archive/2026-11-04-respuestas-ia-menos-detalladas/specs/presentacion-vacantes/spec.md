# Spec Delta

## ADDED Requirements

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
