# Spec Delta

## MODIFIED Requirements

### Requirement: Información organizada de cada vacante
El dashboard SHALL mostrar la información organizada por IA, el puntaje de compatibilidad como estrellas, las razones de coincidencia, los requisitos que no coinciden o no están evidenciados y el enlace a la publicación original.

#### Scenario: Persona consulta una vacante
- **WHEN** la persona revisa una vacante del dashboard
- **THEN** ve la información organizada por IA y puede consultar la publicación en su fuente

#### Scenario: Puntaje representado con estrellas
- **WHEN** el análisis de una vacante tiene un puntaje entre 0 y 10, incluidos decimales
- **THEN** el dashboard representa visualmente su equivalente de 0 a 5 estrellas en pasos de media estrella y conserva el valor numérico exacto en una etiqueta accesible

#### Scenario: Interpretar una media estrella
- **WHEN** la representación del puntaje requiere redondeo a media estrella
- **THEN** el sistema redondea solo la representación visual a la media estrella más cercana y conserva el puntaje exacto para ordenar y filtrar

### Requirement: Ajustar el filtro temporal seleccionando estrellas
El dashboard SHALL permitir ajustar el mínimo temporal del listado mediante opciones seleccionables representadas con estrellas, desde el mínimo guardado en el perfil hasta 5 estrellas. Cada opción SHALL indicar de forma accesible que se muestran puntajes iguales o superiores al valor seleccionado y SHALL aplicarse al seleccionarla, sin botón de confirmación.

#### Scenario: Aplicar el filtro eligiendo estrellas
- **WHEN** la persona selecciona una opción de estrellas
- **THEN** el dashboard aplica el filtro de inmediato y muestra vacantes con puntaje igual o superior al mínimo elegido

#### Scenario: Mantener visible el mínimo del perfil
- **WHEN** la persona abre las recomendaciones sin haber seleccionado un filtro temporal
- **THEN** la opción seleccionada representa el mínimo guardado en el perfil y las opciones adicionales solo permiten elevar ese mínimo

#### Scenario: Traducir estrellas al umbral numérico
- **WHEN** la persona selecciona 2 estrellas
- **THEN** el sistema filtra puntajes de 4/10 o superiores y conserva el puntaje numérico exacto para ordenar

#### Scenario: Usar las opciones con teclado o lector de pantalla
- **WHEN** la persona recorre las opciones del filtro con teclado o lector de pantalla
- **THEN** cada opción comunica el umbral en estrellas y cuál está seleccionada
