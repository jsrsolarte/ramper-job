# Spec Delta

## MODIFIED Requirements

### Requirement: Ofrecer el recorrido inicial solo a cuentas aspirantes
El sistema SHALL iniciar automáticamente el recorrido para una cuenta aspirante en su primer acceso y SHALL exigir completarlo antes de permitir el uso normal de la plataforma; SHALL NOT aplicarlo a cuentas administradoras ni a cuentas que ya habían iniciado sesión antes de activar esta regla.

#### Scenario: Aspirante sin progreso guardado
- **WHEN** una persona aspirante inicia sesión por primera vez y no tiene progreso guardado
- **THEN** el recorrido comienza automáticamente y las funciones normales permanecen bloqueadas hasta que lo complete

#### Scenario: Aspirante con recorrido en curso
- **WHEN** una persona aspirante vuelve a iniciar sesión con el recorrido obligatorio en curso
- **THEN** el sistema reanuda el paso guardado y mantiene bloqueado el uso normal de la plataforma

#### Scenario: Cuenta administradora inicia sesión
- **WHEN** una persona administradora inicia sesión
- **THEN** el sistema no inicia ni ofrece el recorrido de aspirantes ni le exige completarlo

#### Scenario: Aspirante ya había usado la plataforma
- **WHEN** una persona aspirante ya había iniciado sesión antes de activar el recorrido obligatorio
- **THEN** el sistema no bloquea su acceso y le permite abrir la guía desde el encabezado cuando lo desee

### Requirement: Guardar el avance del recorrido por cuenta
El sistema SHALL guardar por cuenta aspirante la versión, el paso actual y el estado del recorrido obligatorio o voluntario para conservar su avance entre dispositivos.

#### Scenario: Aspirante avanza a otro paso
- **WHEN** la persona avanza o retrocede un paso y luego inicia sesión desde otro dispositivo
- **THEN** el sistema reanuda el recorrido en el paso guardado

#### Scenario: Aspirante completa el recorrido
- **WHEN** la persona llega al final del recorrido obligatorio
- **THEN** el sistema guarda su finalización, habilita el uso normal de la plataforma y no vuelve a iniciarlo automáticamente en otros dispositivos

#### Scenario: Aspirante omite el recorrido
- **WHEN** una persona que ya completó el recorrido obligatorio omite una reproducción voluntaria
- **THEN** el sistema guarda ese estado y no vuelve a iniciarlo automáticamente en otros dispositivos

#### Scenario: Aspirante cierra el recorrido antes de terminar
- **WHEN** la persona sale de la sesión o intenta cerrar el recorrido obligatorio sin completarlo
- **THEN** el sistema conserva el paso actual, mantiene bloqueadas las funciones normales y reanuda el recorrido en el siguiente acceso

### Requirement: Volver a abrir el recorrido
El sistema SHALL permitir que una persona aspirante autenticada vuelva a iniciar el recorrido desde un botón permanente del encabezado aunque lo haya completado u omitido.

#### Scenario: Aspirante solicita repasar la guía
- **WHEN** la persona selecciona la opción para volver a ver el recorrido
- **THEN** el sistema inicia la guía desde su primer paso en modo voluntario, sin bloquear el uso normal de la plataforma

#### Scenario: El botón está disponible en las vistas de aspirante
- **WHEN** una persona aspirante autenticada consulta cualquier vista normal de la aplicación
- **THEN** puede abrir la guía desde el botón del encabezado
