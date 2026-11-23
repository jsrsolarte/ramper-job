# Interfaz de usuario Specification

## Purpose

La interfaz ayuda a cada familiar a entender y gestionar su búsqueda laboral con una presentación clara, consistente y utilizable desde computador o móvil.

## Requirements

### Requirement: Presentación visual consistente
Las pantallas de ingreso, dashboard, perfil y administración SHALL compartir la identidad visual de Jobs y una jerarquía que distinga navegación, títulos, contenido y acciones. La identidad SHALL usar el nombre Jobs, recursos gráficos aprobados, la paleta de Jobs, Sora para títulos e identidad e Inter para texto e interfaz.

#### Scenario: Navegación entre pantallas principales
- **WHEN** la persona inicia sesión y navega entre vacantes y perfil
- **THEN** reconoce una estructura de navegación, estilo y acciones coherentes

#### Scenario: Identidad en ingreso y administración
- **WHEN** una persona visita el ingreso o la administración
- **THEN** identifica Jobs mediante su nombre y recursos aprobados y encuentra una presentación coherente con el resto del producto

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

### Requirement: Contraste y estados perceptibles
La interfaz SHALL cumplir WCAG 2.2 AA para el contraste aplicable y SHALL comunicar estados y errores sin depender exclusivamente del color.

#### Scenario: Revisar una acción o mensaje
- **WHEN** una persona consulta acciones, estados o errores en sus superficies reales
- **THEN** el texto y los componentes funcionales tienen contraste suficiente y el significado de los estados también se comunica mediante texto, forma o icono

#### Scenario: Identificar el foco
- **WHEN** una persona navega por teclado en las pantallas de producto y administración
- **THEN** el indicador de foco es visible y distinguible sobre los colores adyacentes

### Requirement: Pie de página centrado con firma secundaria RamPer
El pie de página común SHALL centrarse, usar la paleta visual de Jobs y mostrar la firma «By» junto al lockup claro RamPer v0.6 como elemento secundario, manteniendo Jobs como identidad principal. En el pie, el lockup v0.6 se considera una exploración autorizada exclusivamente para esta superficie; no SHALL declararse como recurso gráfico aprobado ni reutilizarse en otra superficie. La firma RamPer SHALL conservar una alternativa accesible que identifique la marca.

#### Scenario: Consultar una pantalla de Jobs
- **WHEN** una persona abre una pantalla de ingreso, perfil, vacantes, análisis o administración
- **THEN** el pie común aparece centrado, muestra la firma secundaria «By RamPer» y mantiene la identidad Jobs como protagonista

#### Scenario: Consultar el pie en un móvil
- **WHEN** el ancho disponible es reducido
- **THEN** la versión y la firma se reorganizan dentro del pie sin recortarse ni producir desbordamiento horizontal

#### Scenario: Usar tecnología de asistencia
- **WHEN** un lector de pantalla encuentra el lockup RamPer
- **THEN** anuncia un texto alternativo que identifica la marca RamPer sin repetir decoración visual
