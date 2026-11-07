# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Ajustar el mínimo persistente con un control deslizante`
- TO: `### Requirement: Seleccionar el puntaje mínimo con estrellas`

## MODIFIED Requirements

### Requirement: Seleccionar el puntaje mínimo con estrellas
Mi perfil SHALL permitir seleccionar y guardar un puntaje mínimo de compatibilidad eligiendo una opción representada con estrellas, desde cero hasta cinco estrellas, e indicar que se incluyen los puntajes iguales o superiores al seleccionado.

#### Scenario: Cambiar el mínimo guardado
- **WHEN** la persona selecciona una opción de estrellas y guarda el perfil
- **THEN** el sistema guarda ese mínimo persistente y muestra claramente el valor seleccionado como puntaje mínimo

#### Scenario: Elegir cero como mínimo
- **WHEN** la persona elige la opción de cero estrellas y guarda el perfil
- **THEN** el perfil permite mostrar todas las vacantes sin ocultarlas por puntaje

#### Scenario: Usar las opciones con teclado o lector de pantalla
- **WHEN** la persona recorre las opciones con teclado o lector de pantalla
- **THEN** cada opción comunica el umbral en estrellas y cuál está seleccionada

#### Scenario: Guardar una nueva preferencia
- **WHEN** la persona guarda el formulario con un mínimo distinto
- **THEN** el sistema aplica el nuevo mínimo a las siguientes consultas sin volver a analizar las vacantes únicamente por ese cambio y conserva el umbral numérico equivalente internamente
