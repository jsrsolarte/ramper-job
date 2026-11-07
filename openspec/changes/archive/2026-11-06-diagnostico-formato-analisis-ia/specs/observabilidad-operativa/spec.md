# Spec Delta

## ADDED Requirements

### Requirement: Clasificar de forma segura los rechazos de análisis
El sistema SHALL guardar una categoría estable y específica cuando una respuesta de análisis no pueda interpretarse o incumpla la rúbrica, sin registrar el contenido de la respuesta.

#### Scenario: La respuesta incumple una regla de la rúbrica
- **WHEN** el validador rechaza un análisis por versión, estructura, criterio, puntaje, estado o evidencia inválidos
- **THEN** el intento registra una categoría segura que identifica la regla o campo fallido, y el análisis conserva un mensaje genérico para la persona aspirante

#### Scenario: La respuesta no se puede interpretar como JSON
- **WHEN** el contenido devuelto por el modelo no puede interpretarse como JSON
- **THEN** el intento distingue ese fallo de una respuesta JSON válida que incumple la rúbrica

### Requirement: Consultar causas agregadas de rechazos de análisis
El panel operativo SHALL mostrar las categorías seguras y el volumen de rechazos de formato de análisis para el periodo seleccionado, solo a cuentas con acceso administrativo.

#### Scenario: La persona administradora consulta fallos de formato
- **WHEN** existen respuestas rechazadas en el periodo seleccionado
- **THEN** el panel presenta el conteo por categoría segura y permite distinguir errores de interpretación de JSON de incumplimientos de la rúbrica

#### Scenario: No existen rechazos de formato en el periodo
- **WHEN** no hay rechazos de formato durante el periodo seleccionado
- **THEN** el panel indica que no hay fallos de este tipo en el intervalo

### Requirement: Proteger los datos al registrar fallos de formato
El sistema SHALL NOT guardar en categorías, métricas ni mensajes de error el CV, texto del perfil, prompts, credenciales ni la respuesta completa del modelo.

#### Scenario: Se registra el motivo de una validación fallida
- **WHEN** el sistema conserva el diagnóstico de una respuesta rechazada
- **THEN** almacena únicamente una categoría controlada y metadatos técnicos permitidos, sin fragmentos de la solicitud o respuesta
