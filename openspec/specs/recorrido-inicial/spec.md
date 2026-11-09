# Recorrido inicial Specification

## Purpose

Orienta a las personas aspirantes durante la configuración inicial de su búsqueda laboral y les enseña a interpretar y organizar sus vacantes. Conserva el avance por cuenta para que la guía pueda continuar entre dispositivos y consultarse nuevamente.

## Requirements

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

### Requirement: Explicar la configuración del perfil de búsqueda
El recorrido SHALL explicar cómo cargar el CV y definir frases de búsqueda, ubicaciones, preferencia de trabajo remoto y descarte automático por puntaje, sin cambiar los datos del perfil.

#### Scenario: Aspirante recorre la configuración inicial
- **WHEN** la persona avanza por los pasos de configuración del perfil
- **THEN** la guía explica la carga del CV, los cargos o áreas buscados, las ubicaciones, la opción de trabajo remoto y el umbral de descarte automático

#### Scenario: Aspirante consulta el umbral de descarte
- **WHEN** la guía explica el descarte automático
- **THEN** indica que las vacantes nuevas con puntaje inferior al umbral guardado pasan a Descartadas, que el valor cero desactiva esta regla y que cambiar el valor no modifica vacantes ya encontradas

#### Scenario: Aspirante avanza sin editar el perfil
- **WHEN** la persona avanza, reanuda u omite un paso del recorrido
- **THEN** el sistema conserva sin cambios el CV, las frases, las ubicaciones, la preferencia de trabajo remoto y el umbral guardados

### Requirement: Guiar la navegación entre vacantes y Mi perfil
El recorrido SHALL comenzar en Recomendaciones enseñando cómo abrir Mi perfil, SHALL explicar allí toda la configuración del perfil, y luego SHALL enseñar cómo volver a Recomendaciones antes de continuar con los pasos del dashboard, conservando el avance al activar los enlaces.

#### Scenario: Aspirante entra a Mi perfil desde sus vacantes
- **WHEN** la persona llega al paso que destaca el enlace Mi perfil en el dashboard y lo activa
- **THEN** el recorrido guarda y muestra el primer paso de configuración del perfil

#### Scenario: Aspirante vuelve a sus vacantes desde Mi perfil
- **WHEN** la persona llega al paso que destaca Volver a mis vacantes en el perfil y lo activa
- **THEN** el recorrido guarda el avance, vuelve a Recomendaciones y muestra el siguiente paso del dashboard

#### Scenario: Aspirante comienza el recorrido desde Recomendaciones
- **WHEN** una persona inicia el recorrido
- **THEN** el primer paso destaca el enlace Mi perfil antes de explicar los controles del perfil

#### Scenario: Aspirante termina de revisar su perfil
- **WHEN** la persona llega al paso de volver a sus vacantes después de revisar todos los controles del perfil
- **THEN** el siguiente paso aparece en Recomendaciones y el recorrido continúa con el dashboard

### Requirement: Explicar resultados y pestañas de vacantes
El recorrido SHALL explicar cómo interpretar las compatibilidades, consultar detalles del análisis y organizar las vacantes según sus pestañas y estados.

#### Scenario: Aspirante consulta resultados
- **WHEN** la persona recorre los pasos del dashboard
- **THEN** la guía explica las estrellas de compatibilidad, dónde consultar vacantes por analizar y dónde ver recomendaciones con puntaje

#### Scenario: Aspirante consulta las pestañas de seguimiento
- **WHEN** la guía explica las pestañas del dashboard
- **THEN** describe Aplicadas, En proceso, Entrevista, Finalizadas y Descartadas como estados de seguimiento de vacantes

#### Scenario: Aspirante distingue el filtro de estrellas del descarte automático
- **WHEN** la guía explica el filtro temporal de recomendaciones por estrellas
- **THEN** indica que el filtro solo cambia las recomendaciones visibles y no modifica el umbral guardado ni el estado de ninguna vacante

#### Scenario: Aspirante consulta el detalle de compatibilidad
- **WHEN** la persona sigue el paso que explica una tarjeta de recomendación
- **THEN** la guía indica que puede abrir los detalles del análisis para revisar razones de coincidencia y aspectos por revisar

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

### Requirement: Usar el recorrido con distintos tamaños de pantalla y métodos de entrada
El recorrido SHALL mantener sus pasos, controles y contenido comprensibles y utilizables en pantallas pequeñas y mediante teclado.

#### Scenario: Aspirante sigue la guía desde un móvil
- **WHEN** la persona abre un paso del recorrido en una pantalla estrecha
- **THEN** el contenido y los controles de la guía caben en pantalla y el elemento explicado sigue identificable

#### Scenario: Aspirante navega el recorrido con teclado
- **WHEN** la persona usa el teclado para avanzar, retroceder u omitir la guía
- **THEN** puede identificar el foco y activar cada control disponible
