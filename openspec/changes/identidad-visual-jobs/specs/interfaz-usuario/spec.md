# Spec Delta

## MODIFIED Requirements

### Requirement: Presentación visual consistente
Las pantallas de ingreso, dashboard, perfil y administración SHALL compartir la identidad visual de Jobs y una jerarquía que distinga navegación, títulos, contenido y acciones. La identidad SHALL usar el nombre Jobs, recursos gráficos aprobados, la paleta de Jobs, Sora para títulos e identidad e Inter para texto e interfaz.

#### Scenario: Navegación entre pantallas principales
- **WHEN** la persona inicia sesión y navega entre vacantes y perfil
- **THEN** reconoce una estructura de navegación, estilo y acciones coherentes

#### Scenario: Identidad en ingreso y administración
- **WHEN** una persona visita el ingreso o la administración
- **THEN** identifica Jobs mediante su nombre y recursos aprobados y encuentra una presentación coherente con el resto del producto

## ADDED Requirements

### Requirement: Contraste y estados perceptibles
La interfaz SHALL cumplir WCAG 2.2 AA para el contraste aplicable y SHALL comunicar estados y errores sin depender exclusivamente del color.

#### Scenario: Revisar una acción o mensaje
- **WHEN** una persona consulta acciones, estados o errores en sus superficies reales
- **THEN** el texto y los componentes funcionales tienen contraste suficiente y el significado de los estados también se comunica mediante texto, forma o icono

#### Scenario: Identificar el foco
- **WHEN** una persona navega por teclado en las pantallas de producto y administración
- **THEN** el indicador de foco es visible y distinguible sobre los colores adyacentes
