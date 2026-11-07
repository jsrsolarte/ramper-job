# Spec Delta

## ADDED Requirements

### Requirement: Ajustar el mínimo persistente con un control deslizante
Mi perfil SHALL permitir seleccionar un puntaje mínimo entero de 0 a 10 con un control deslizante accesible y mostrar que se incluyen los puntajes iguales o superiores al seleccionado.

#### Scenario: Cambiar el mínimo guardado
- **WHEN** la persona mueve el control a un valor entero entre 0 y 10 y guarda el perfil
- **THEN** el sistema guarda ese mínimo persistente y muestra claramente el valor seleccionado seguido de “o más”

#### Scenario: Elegir cero como mínimo
- **WHEN** la persona mueve el control a 0 y guarda el perfil
- **THEN** el perfil permite mostrar todas las vacantes sin ocultarlas por puntaje

#### Scenario: Ajustar el control mediante teclado
- **WHEN** la persona enfoca el control con teclado y cambia su valor
- **THEN** puede seleccionar los valores enteros de 0 a 10 y percibir el valor actual mediante una etiqueta accesible

#### Scenario: Guardar una nueva preferencia
- **WHEN** la persona guarda el formulario con un mínimo distinto
- **THEN** el sistema aplica el nuevo mínimo a las siguientes consultas sin volver a analizar las vacantes únicamente por ese cambio
