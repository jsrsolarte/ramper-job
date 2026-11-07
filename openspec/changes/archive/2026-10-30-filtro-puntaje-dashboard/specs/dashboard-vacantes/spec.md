# Spec Delta

## ADDED Requirements

### Requirement: Filtrar vacantes por puntaje en el dashboard
El dashboard SHALL permitir aplicar al listado un puntaje mínimo temporal sin modificar las preferencias guardadas del perfil.

#### Scenario: Se muestran todas las vacantes permitidas por el perfil
- **WHEN** la persona elige la opción para ver todas las vacantes permitidas
- **THEN** el dashboard muestra las vacantes que cumplen el puntaje mínimo configurado en el perfil

#### Scenario: La persona eleva el mínimo del listado
- **WHEN** la persona elige un puntaje mínimo superior al configurado en el perfil
- **THEN** el dashboard muestra solo vacantes cuyo puntaje sea igual o superior al umbral elegido

#### Scenario: El umbral del listado está por debajo del perfil
- **WHEN** la persona envía un puntaje mínimo inferior al configurado en el perfil
- **THEN** el dashboard conserva el mínimo del perfil como umbral efectivo y no muestra vacantes excluidas por el perfil

#### Scenario: Cambiar el filtro no modifica el perfil
- **WHEN** la persona cambia el umbral temporal del listado
- **THEN** el puntaje mínimo guardado en el perfil permanece sin cambios

### Requirement: Conservar el filtro de puntaje al navegar el listado
El dashboard SHALL conservar el umbral temporal seleccionado al cambiar de página y al recargar el listado.

#### Scenario: Cambiar de página con un umbral activo
- **WHEN** la persona avanza o retrocede una página del listado filtrado
- **THEN** el listado conserva el mismo umbral temporal seleccionado

### Requirement: Validar el puntaje mínimo temporal
El dashboard SHALL aceptar únicamente umbrales de puntaje entre 0 y 10 y descartar valores inválidos sin relajar el mínimo del perfil.

#### Scenario: Puntaje fuera del rango
- **WHEN** se solicita un umbral menor que 0, mayor que 10 o no numérico
- **THEN** el dashboard aplica el mínimo del perfil como umbral efectivo y presenta el listado sin error
