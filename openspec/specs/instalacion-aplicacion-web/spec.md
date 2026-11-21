# instalacion-aplicacion-web Specification

## Purpose

Permite instalar Jobs desde Chrome y abrirlo como aplicación web identificable en el dispositivo.

## Requirements

### Requirement: Permitir la instalación desde Chrome
El sistema SHALL ofrecer los recursos necesarios para que Chrome permita instalar Jobs en computador y Android desde su interfaz de instalación, cuando se cumplan los requisitos del navegador y del entorno seguro.

#### Scenario: Instalar desde el navegador
- **WHEN** una persona visita Jobs en una versión compatible de Chrome mediante HTTPS y selecciona instalar
- **THEN** Chrome ofrece instalar la aplicación con el nombre Jobs e icono oficial aprobado de Jobs

#### Scenario: La persona no instala
- **WHEN** la persona ignora o cancela la instalación
- **THEN** puede seguir usando el sitio web normalmente

#### Scenario: Actualizar una instalación existente
- **WHEN** se actualizan el nombre y los iconos de una instalación existente en el mismo origen
- **THEN** la identidad estable de la instalación se conserva y la actualización no requiere crear otra aplicación

### Requirement: Abrir la aplicación instalada
La aplicación instalada SHALL abrir la página inicial de Jobs en una presentación independiente y conservar el flujo normal de autenticación y autorización.

#### Scenario: Apertura sin sesión
- **WHEN** se abre la aplicación instalada sin una sesión válida
- **THEN** se presenta el inicio de sesión y las páginas privadas siguen protegidas

#### Scenario: Apertura con sesión válida
- **WHEN** se abre la aplicación instalada con una sesión válida
- **THEN** la persona llega al destino habitual de su cuenta y puede navegar y cerrar sesión

### Requirement: Mantener acceso y privacidad
La instalación SHALL ser opcional y no SHALL almacenar datos privados de perfiles, vacantes o CV para uso sin conexión.

#### Scenario: Se pierde la conexión
- **WHEN** una persona abre o utiliza la aplicación sin conexión
- **THEN** no se presenta información privada almacenada por la funcionalidad de instalación ni se promete que las operaciones se completaron

#### Scenario: Cierre de sesión o cambio de cuenta
- **WHEN** una persona cierra sesión y otra abre la aplicación instalada
- **THEN** se aplican los controles de acceso habituales sin revelar datos privados de la sesión anterior mediante una caché de instalación
