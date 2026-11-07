# Spec Delta

## MODIFIED Requirements

### Requirement: Análisis por perfil mediante el servicio de IA
El sistema SHALL solicitar al modelo de IA configurado mediante OmniRoute un puntaje de compatibilidad por perfil, separado de la organización de la publicación. Una vez guardado el puntaje, SHALL solicitar la organización de la publicación de forma asíncrona cuando alcance el mínimo vigente del perfil.

#### Scenario: Vacante analizada para un perfil
- **WHEN** existe una vacante elegible y un perfil con CV y preferencias vigentes
- **THEN** el sistema solicita primero el puntaje de compatibilidad y conserva el resultado aunque la organización siga pendiente

#### Scenario: Puntaje alcanza el mínimo del perfil
- **WHEN** el puntaje guardado es igual o superior al mínimo vigente del perfil
- **THEN** el sistema encola la organización de la publicación sin retrasar la disponibilidad del puntaje

#### Scenario: Puntaje queda bajo el mínimo del perfil
- **WHEN** el puntaje guardado es inferior al mínimo vigente del perfil
- **THEN** el sistema conserva el puntaje y sus razones sin solicitar todavía la organización de la publicación

#### Scenario: El mínimo del perfil disminuye
- **WHEN** una persona reduce su mínimo y existen puntajes guardados que ahora lo alcanzan sin organización disponible
- **THEN** el sistema encola la organización pendiente de esos resultados

#### Scenario: Servicio de IA no disponible
- **WHEN** OmniRoute o el modelo configurado no devuelve un puntaje utilizable
- **THEN** el sistema no inventa una clasificación y deja la etapa de puntuación pendiente para reintento

#### Scenario: Organización falla después de puntuar
- **WHEN** OmniRoute o el modelo configurado no devuelve una organización utilizable
- **THEN** el sistema conserva el puntaje y deja pendiente para reintento solo la etapa de organización

#### Scenario: Cambia la configuración activa antes de reintentar una organización fallida
- **WHEN** una organización falló con una configuración que ya no está activa
- **THEN** el reintento automático no vuelve a invocar el prompt reemplazado y conserva el registro histórico del fallo

### Requirement: Resultado explicable de compatibilidad
El sistema SHALL conservar para cada análisis un puntaje de 0.0 a 10.0 con una cifra decimal, razones de coincidencia y requisitos no coincidentes o no evidenciados en el CV.

#### Scenario: Análisis completo
- **WHEN** el modelo devuelve un puntaje válido
- **THEN** el resultado incluye el puntaje, el desglose por criterios, razones de coincidencia y requisitos no coincidentes o no evidenciados, aunque la organización de la publicación siga pendiente o se haya omitido por el mínimo

### Requirement: Descripción organizada por IA
El sistema SHALL generar información organizada de la vacante basada en la publicación original y diferenciada de ella.

#### Scenario: Descripción organizada disponible
- **WHEN** la etapa asíncrona de organización termina correctamente
- **THEN** el sistema conserva el contenido organizado por IA junto con la referencia a la publicación original

### Requirement: Configuración ajustable y versionada
El sistema SHALL permitir a una persona administradora ajustar y versionar los prompts y parámetros usados para generar búsquedas y evaluar compatibilidad.

#### Scenario: Administrador modifica la configuración
- **WHEN** una persona administradora guarda cambios en un prompt o parámetro
- **THEN** el sistema crea una nueva versión para los procesos siguientes sin alterar los resultados ya generados

#### Scenario: Se reprocesa una vacante
- **WHEN** una persona administradora solicita reprocesar una vacante para un perfil
- **THEN** el sistema crea un nuevo análisis con las versiones vigentes del perfil y la configuración, y conserva el resultado previo para trazabilidad

## ADDED Requirements

### Requirement: Reutilizar la organización para una vacante y configuración
El sistema SHALL reutilizar una organización válida para la misma vacante y configuración vigente, evitando repetir esa etapa por cada perfil.

#### Scenario: Varios perfiles alcanzan su mínimo para la misma vacante
- **WHEN** más de un perfil requiere la organización de una vacante con la misma configuración
- **THEN** el sistema ejecuta una sola organización reutilizable y la pone a disposición de todos los análisis que la requieren

#### Scenario: Cambia la configuración de organización
- **WHEN** la configuración usada para organizar cambia
- **THEN** el sistema genera y reutiliza una organización correspondiente a la nueva configuración sin reemplazar resultados históricos

### Requirement: Registrar consumo y duración de cada etapa
El sistema SHALL conservar por llamada de IA la etapa, duración y tokens reportados por el proveedor, vinculados al análisis o a la organización reutilizable.

#### Scenario: El proveedor informa uso de tokens
- **WHEN** una llamada de puntuación u organización termina y el proveedor informa tokens de entrada y salida
- **THEN** el sistema conserva esos valores junto con la etapa y la duración de la llamada

#### Scenario: El proveedor no informa uso de tokens
- **WHEN** una llamada termina sin datos de tokens utilizables
- **THEN** el sistema registra el uso como no disponible y no como cero

#### Scenario: Uso disponible para agregación operativa
- **WHEN** los registros de llamadas se consultan para métricas agregadas
- **THEN** pueden agruparse por etapa y resultado sin acceder a CV, texto de perfil, prompts ni respuestas completas
