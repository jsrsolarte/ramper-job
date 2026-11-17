## ADDED Requirements

### Requirement: Permitir guardar Mi perfil durante el recorrido obligatorio
El sistema SHALL permitir guardar cambios válidos de «Mi perfil» cuando el paso actual del recorrido obligatorio corresponde a la configuración del perfil, sin completar ni avanzar automáticamente el recorrido.

#### Scenario: Aspirante guarda cambios válidos del perfil
- **WHEN** una persona aspirante envía datos válidos de su perfil durante un paso de configuración del perfil
- **THEN** el sistema guarda el CV y las preferencias válidas, vuelve a mostrar «Mi perfil» y conserva el recorrido en el paso actual

#### Scenario: El formulario contiene datos inválidos
- **WHEN** una persona aspirante envía el formulario de perfil con errores de validación durante un paso de configuración del perfil
- **THEN** el sistema muestra los errores, no guarda los cambios inválidos y conserva el recorrido en el paso actual

#### Scenario: La persona intenta usar otra función antes de completar la guía
- **WHEN** el recorrido obligatorio continúa activo y la persona navega a una función normal distinta de «Mi perfil»
- **THEN** el sistema mantiene bloqueada esa función hasta que la persona complete el recorrido
