# Spec Delta

## ADDED Requirements

### Requirement: Ajustar el filtro temporal con un control deslizante
El dashboard SHALL permitir ajustar el mínimo temporal del listado con un control deslizante entero desde el mínimo guardado en el perfil hasta 10, indicando que se muestran puntajes iguales o superiores al valor seleccionado.

#### Scenario: Mostrar todas las vacantes permitidas por el perfil
- **WHEN** la persona deja el control en el mínimo guardado en su perfil
- **THEN** el dashboard muestra todas las vacantes permitidas por ese mínimo y etiqueta el valor como “X/10 o más”

#### Scenario: Elevar el mínimo temporal
- **WHEN** la persona mueve el control a un valor entero superior al mínimo del perfil
- **THEN** el dashboard muestra solo vacantes con un puntaje igual o superior al valor temporal seleccionado

#### Scenario: Aplicar el cambio del control automáticamente
- **WHEN** la persona termina de mover el control o cambia su valor con el teclado
- **THEN** el dashboard aplica el filtro seleccionado sin requerir un botón de confirmación

#### Scenario: Conservar la preferencia del perfil
- **WHEN** la persona cambia el control temporal del dashboard
- **THEN** el sistema modifica solo el filtro del listado y conserva el mínimo persistente del perfil

#### Scenario: Cambiar el filtro con teclado
- **WHEN** la persona enfoca el control con teclado y cambia su valor
- **THEN** puede seleccionar valores enteros permitidos y percibir el umbral actual mediante una etiqueta accesible

#### Scenario: Conservar el filtro al paginar
- **WHEN** la persona avanza o retrocede una página del listado filtrado
- **THEN** el dashboard conserva el mismo umbral temporal seleccionado
