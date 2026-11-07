# Spec Delta

## Purpose

La interfaz ayuda a cada familiar a entender y gestionar su búsqueda laboral con una presentación clara, consistente y usable desde computador o móvil.

## ADDED Requirements

### Requirement: Presentación visual consistente
Las pantallas de ingreso, dashboard y perfil SHALL compartir una identidad visual coherente y una jerarquía tipográfica que distinga navegación, títulos, contenido y acciones.

#### Scenario: Navegación entre pantallas principales
- **WHEN** la persona inicia sesión y navega entre vacantes y perfil
- **THEN** reconoce una estructura de navegación, estilo y acciones coherentes en ambas pantallas

### Requirement: Lectura rápida de vacantes
El dashboard SHALL destacar el puntaje de compatibilidad y los datos concretos de la vacante, mostrar sus palabras clave concisas y mantener las razones y aspectos por revisar en segundo plano.

#### Scenario: Comparar vacantes recomendadas
- **WHEN** se muestran una o más vacantes analizadas
- **THEN** cada tarjeta permite identificar el cargo, empresa, ubicación y condiciones principales, y consultar aparte los detalles del análisis

### Requirement: Uso adaptable y accesible
Las pantallas principales SHALL conservar su contenido y acciones utilizables en pantallas pequeñas, con controles legibles, etiquetas visibles y estados de foco identificables al navegar con teclado.

#### Scenario: Consultar desde un móvil
- **WHEN** una persona abre el dashboard o edita su perfil en una pantalla estrecha
- **THEN** el contenido se reorganiza sin desbordamiento horizontal y las acciones principales siguen disponibles

#### Scenario: Navegar mediante teclado
- **WHEN** una persona recorre los controles de ingreso, navegación o edición del perfil con el teclado
- **THEN** puede identificar el control enfocado y distinguir sus etiquetas y mensajes de estado
