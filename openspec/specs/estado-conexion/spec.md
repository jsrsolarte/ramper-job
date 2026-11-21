# Estado de conexión Specification

## Purpose

Permite entender si Ramper Job está disponible y actuar con claridad cuando una conexión interrumpida afecta una operación.

## Requirements

### Requirement: Informar la pérdida de acceso
El sistema SHALL mostrar un aviso accesible y persistente cuando detecte que el navegador está sin conexión o que no puede comunicarse con Ramper Job.

#### Scenario: Se pierde la conexión con la página abierta
- **WHEN** el navegador informa que ha perdido la conexión
- **THEN** la pantalla indica que la aplicación necesita conexión y no puede garantizar que se guarden cambios

#### Scenario: El navegador tiene red pero el servicio no responde
- **WHEN** una comprobación del servicio falla o excede su tiempo límite
- **THEN** la pantalla indica que no puede contactar Ramper Job sin atribuir la causa a la conexión de internet

### Requirement: Confirmar la recuperación del servicio
El sistema SHALL comprobar nuevamente la disponibilidad y actualizar el aviso cuando el servicio responda, sin afirmar que una operación anterior se guardó.

#### Scenario: El navegador recupera la red
- **WHEN** vuelve la conexión de red y el servicio responde a una comprobación
- **THEN** el aviso informa que se recuperó el acceso y deja de presentar el servicio como inaccesible

#### Scenario: La red vuelve pero el servicio sigue inaccesible
- **WHEN** el navegador informa que hay red pero la comprobación del servicio falla
- **THEN** el aviso permanece e indica que Ramper Job sigue sin responder

### Requirement: Tratar con cautela las operaciones interrumpidas
El sistema SHALL evitar confirmar o reenviar automáticamente una operación de escritura cuyo resultado no se ha recibido y SHALL orientar a la persona para verificar el resultado antes de reintentarlo.

#### Scenario: Falla una operación sin respuesta confirmada
- **WHEN** se interrumpe la comunicación durante una operación de guardado
- **THEN** el sistema informa que el resultado es incierto y aconseja comprobarlo antes de repetir la acción

#### Scenario: El formulario sigue abierto
- **WHEN** se pierde el acceso antes de enviar un formulario que permanece en pantalla
- **THEN** el aviso no borra sus campos y la persona puede conservarlos en la página mientras verifica la conexión

### Requirement: Mantener el uso normal y proteger datos
El sistema SHALL mantener el funcionamiento habitual cuando no exista evidencia de fallo y SHALL NOT almacenar datos personales para permitir uso sin conexión.

#### Scenario: Hay acceso normal
- **WHEN** el servicio está disponible
- **THEN** la navegación y los formularios funcionan sin un aviso persistente de desconexión

#### Scenario: La página no se ha podido abrir
- **WHEN** la aplicación no está cargada y el dispositivo no puede acceder al servidor
- **THEN** no se promete mostrar el aviso dentro de la aplicación ni acceder a contenido privado
