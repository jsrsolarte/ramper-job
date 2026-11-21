## ADDED Requirements

### Requirement: Obtener vacantes públicas de Computrabajo Colombia
El sistema SHALL obtener publicaciones públicas de Computrabajo Colombia y normalizarlas al formato común, conservando la fuente y el enlace original.

#### Scenario: Tarjeta de una vacante disponible
- **WHEN** una consulta devuelve una tarjeta interpretable de Computrabajo
- **THEN** el sistema conserva el identificador externo, título, enlace y los datos disponibles de empresa, ubicación, salario y antigüedad

#### Scenario: Falta un dato en la tarjeta
- **WHEN** la tarjeta no informa un campo opcional
- **THEN** el sistema lo deja como desconocido sin inferirlo de la búsqueda

### Requirement: Enriquecer las publicaciones de Computrabajo
El sistema SHALL consultar la ficha pública de cada publicación única de Computrabajo y conservar los detalles disponibles sin perder los datos del listado.

#### Scenario: La ficha incluye condiciones y requisitos
- **WHEN** la ficha proporciona descripción, contrato, jornada, modalidad, formación o experiencia
- **THEN** el sistema conserva los datos disponibles en el formato común y mantiene los valores del listado cuando difieren

#### Scenario: La ficha no está disponible
- **WHEN** una ficha individual falla por un error temporal, vence el tiempo de espera o no se puede interpretar sin recibir una respuesta de bloqueo
- **THEN** el sistema conserva los datos del listado y continúa con las demás fichas de Computrabajo

### Requirement: Configurar el User-Agent de Computrabajo
El sistema SHALL permitir configurar el User-Agent utilizado en las consultas del listado y las fichas de Computrabajo, con un valor inicial compatible con el usado en la prueba compartida.

#### Scenario: Se cambia la configuración
- **WHEN** se configura un User-Agent distinto para Computrabajo
- **THEN** las siguientes solicitudes de esa fuente usan el valor configurado

### Requirement: Registrar fallos de Computrabajo
El sistema SHALL indicar la indisponibilidad de Computrabajo cuando una búsqueda o ficha sea bloqueada y SHALL permitir que las demás fuentes continúen.

#### Scenario: La fuente rechaza la búsqueda
- **WHEN** Computrabajo devuelve HTTP 403, 401 o 429 o exige autenticación para la búsqueda pública
- **THEN** el sistema detiene las siguientes solicitudes a Computrabajo en esa ejecución, registra la fuente como no disponible y no intenta evadir el control

#### Scenario: Una ficha bloquea las consultas de la fuente
- **WHEN** una ficha de Computrabajo responde HTTP 401, 403 o 429 durante una ejecución
- **THEN** el sistema conserva los datos de listado obtenidos, detiene las siguientes solicitudes a Computrabajo en esa ejecución y registra la fuente como no disponible

#### Scenario: Falla una fuente y otra responde
- **WHEN** Computrabajo no está disponible y El Empleo responde normalmente
- **THEN** el sistema conserva y procesa los resultados de El Empleo

### Requirement: Deduplicar publicaciones de Computrabajo
El sistema SHALL identificar cada publicación de Computrabajo por su identificador externo cuando esté disponible y reutilizar el flujo común de deduplicación y análisis por perfil.

#### Scenario: Una publicación aparece en varias búsquedas
- **WHEN** dos consultas devuelven la misma publicación de Computrabajo con el mismo identificador
- **THEN** el sistema conserva un único registro de esa fuente y mantiene los seguimientos y análisis existentes por perfil
