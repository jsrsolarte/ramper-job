# Observabilidad operativa Specification

## Purpose

Da al personal administrador una vista agregada del estado y la evolución de la ingesta y el análisis de vacantes. Conserva suficiente historial operativo para entender volúmenes, tiempos y fallas sin exponer datos de perfiles.

## Requirements

### Requirement: Restringir las métricas operativas a administración
El sistema SHALL permitir consultar el panel operativo únicamente a cuentas autorizadas para administrar la plataforma.

#### Scenario: Una persona administradora abre el panel
- **WHEN** una cuenta con acceso administrativo consulta el panel operativo
- **THEN** el sistema muestra las métricas agregadas disponibles

#### Scenario: Una cuenta de aspirante intenta abrir el panel
- **WHEN** una cuenta sin permisos administrativos solicita el panel operativo
- **THEN** el sistema deniega el acceso sin revelar métricas ni información privada

### Requirement: Consultar métricas históricas de fuentes
El panel SHALL mostrar por fuente el volumen de ejecuciones, resultados, vacantes encontradas y duración durante un periodo seleccionable.

#### Scenario: Hay historial de consultas de una fuente
- **WHEN** la persona administradora selecciona un periodo con ejecuciones registradas
- **THEN** el panel muestra conteos de ejecuciones exitosas y fallidas, vacantes encontradas y tiempo promedio de ejecución para cada fuente

#### Scenario: Una fuente presenta fallas
- **WHEN** se registra una consulta fallida o parcial durante el periodo
- **THEN** el panel muestra su frecuencia, el último éxito y un resumen seguro del error más reciente

#### Scenario: No hay historial para el periodo
- **WHEN** una fuente no tiene ejecuciones registradas en el periodo elegido
- **THEN** el panel indica que no hay datos para ese periodo y presenta desde cuándo existe instrumentación

### Requirement: Consultar métricas y antigüedad de análisis
El panel SHALL mostrar los análisis completados, pendientes, reemplazados, fallidos o reintentados y sus tiempos durante el periodo seleccionado.

#### Scenario: Hay análisis completados
- **WHEN** existen análisis completados en el periodo elegido
- **THEN** el panel muestra el volumen completado y el tiempo promedio entre inicio y finalización

#### Scenario: Hay trabajo pendiente
- **WHEN** existen análisis pendientes del periodo o de periodos anteriores
- **THEN** el panel muestra la cantidad pendiente y la antigüedad del pendiente más antiguo

#### Scenario: Hay fallas o reintentos
- **WHEN** existen intentos fallidos o análisis con error durante el periodo
- **THEN** el panel muestra su cantidad y proporción, junto con un resumen seguro de los errores recientes

### Requirement: Filtrar métricas y mostrar su cobertura
El panel SHALL permitir consultar métricas para periodos de 24 horas, 7 días o 30 días e indicar el intervalo y la fecha desde la que hay historial disponible.

#### Scenario: La persona cambia el periodo
- **WHEN** la persona administradora selecciona otro periodo
- **THEN** los conteos y tiempos se recalculan para el intervalo elegido

#### Scenario: Los registros históricos son anteriores a la instrumentación
- **WHEN** se consultan datos generados antes de que se empezara a registrar historial operativo
- **THEN** el panel no los presenta como métricas históricas completas y muestra la fecha inicial de cobertura

### Requirement: Proteger los datos de perfiles en métricas
El panel SHALL presentar métricas agregadas y SHALL NOT exponer CV, textos de perfil, prompts, credenciales ni contenido completo de vacantes.

#### Scenario: Se muestra un error operativo
- **WHEN** el panel presenta un error de una fuente o un análisis
- **THEN** muestra un resumen sin credenciales, datos del CV ni contenido privado del perfil

### Requirement: Cerrar ejecuciones interrumpidas
La limpieza periódica SHALL marcar como fallidas las ejecuciones que permanezcan en curso por más de 20 minutos, con una categoría segura que identifique la interrupción.

#### Scenario: Un worker se detiene durante una ejecución
- **WHEN** una ejecución sigue marcada en curso por más de 20 minutos
- **THEN** la limpieza registra su finalización y un resumen seguro de interrupción sin borrar el historial

### Requirement: Diferenciar trabajo pendiente de trabajo en ejecución
El dashboard de aspirantes SHALL identificar como pendientes las vacantes que esperan análisis y SHALL NOT afirmar que están siendo procesadas mientras solo estén en cola.

#### Scenario: Hay vacantes en espera
- **WHEN** existen análisis pendientes para la revisión y ubicación actuales del perfil
- **THEN** el dashboard muestra cuántas vacantes están pendientes de análisis

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
