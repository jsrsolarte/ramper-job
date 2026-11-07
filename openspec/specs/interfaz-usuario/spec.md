# Interfaz de usuario Specification

## Purpose

La interfaz ayuda a cada familiar a entender y gestionar su búsqueda laboral con una presentación clara, consistente y utilizable desde computador o móvil.

## Requirements

### Requirement: Presentación visual consistente
Las pantallas de ingreso, dashboard y perfil SHALL compartir una identidad visual coherente y una jerarquía que distinga navegación, títulos, contenido y acciones.

#### Scenario: Navegación entre pantallas principales
- **WHEN** la persona inicia sesión y navega entre vacantes y perfil
- **THEN** reconoce una estructura de navegación, estilo y acciones coherentes

### Requirement: Lectura rápida de vacantes
El dashboard SHALL destacar el puntaje y organizar la tarjeta para que la persona identifique el cargo, la empresa, la ubicación y las condiciones principales.

#### Scenario: Comparar vacantes recomendadas
- **WHEN** se muestran vacantes analizadas
- **THEN** cada tarjeta permite distinguir el puntaje y los datos principales, con las palabras clave visibles y los motivos de análisis en segundo plano

### Requirement: Uso adaptable y accesible
Las pantallas principales SHALL conservar su contenido y acciones utilizables en pantallas pequeñas, con controles legibles, etiquetas visibles y foco identificable mediante teclado.

#### Scenario: Consultar desde un móvil
- **WHEN** una persona abre el dashboard o edita su perfil en una pantalla estrecha
- **THEN** el contenido se reorganiza sin desbordamiento horizontal y las acciones principales siguen disponibles

#### Scenario: Navegar mediante teclado
- **WHEN** una persona recorre los controles principales con el teclado
- **THEN** puede identificar el control enfocado y distinguir sus etiquetas y mensajes de estado
