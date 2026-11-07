# Compatibilidad de vacantes Specification

## Purpose

Evalúa qué tan bien se ajusta una vacante al CV y las preferencias de una persona, y prepara información legible para apoyar su búsqueda laboral.

## Requirements

### Requirement: Análisis por perfil mediante el servicio de IA
El sistema SHALL solicitar al modelo de IA configurado mediante OmniRoute un puntaje de compatibilidad por perfil separado de la organización de la publicación. Una vez guardado el puntaje, SHALL solicitar la organización de forma asíncrona cuando alcance el mínimo vigente del perfil.

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
- **WHEN** OmniRoute o el modelo configurado no devuelve un análisis utilizable
- **THEN** el sistema conserva el análisis pendiente y lo vuelve a encolar con espera creciente limitada hasta el vencimiento configurado

#### Scenario: Organización falla después de puntuar
- **WHEN** OmniRoute o el modelo configurado no devuelve una organización utilizable
- **THEN** el sistema conserva el puntaje y deja pendiente para reintento solo la etapa de organización

#### Scenario: Cambia la configuración activa antes de reintentar una organización fallida
- **WHEN** una organización falló con una configuración que ya no está activa
- **THEN** el reintento automático no vuelve a invocar el prompt reemplazado y conserva el registro histórico del fallo

#### Scenario: Vence el plazo de análisis
- **WHEN** el análisis no puede completarse dentro de los días configurados desde el primer hallazgo para el perfil
- **THEN** el sistema deja de reencolarlo y descarta la vacante para ese perfil sin borrar la publicación compartida

### Requirement: Resultado explicable de compatibilidad
El sistema SHALL conservar para cada análisis un puntaje de 0.0 a 10.0 con una cifra decimal, el desglose y evidencia de la rúbrica, razones de coincidencia, requisitos críticos y deducciones aplicadas.

#### Scenario: Análisis completo
- **WHEN** el modelo devuelve un desglose válido para todos los criterios
- **THEN** el resultado incluye el puntaje calculado por el sistema, el desglose por criterios, razones y requisitos no coincidentes o no evidenciados aunque la organización siga pendiente o se haya omitido por el mínimo

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

### Requirement: Evaluación con una rúbrica fija y versionada
El sistema SHALL enviar al modelo una rúbrica común y versionada, y exigir una evaluación por criterio con puntaje de hasta una cifra decimal, estado de evidencia y soporte basado en el CV y la vacante.

#### Scenario: Se evalúa una vacante elegible
- **WHEN** el sistema solicita un análisis de compatibilidad
- **THEN** envía la misma versión vigente de la rúbrica para todos los perfiles y vacantes analizados con esa configuración

#### Scenario: Se evalúa una habilidad o experiencia requerida
- **WHEN** el modelo evalúa los criterios de la rúbrica
- **THEN** asigna hasta una cifra decimal dentro de los máximos de cada criterio: 4 para competencias y habilidades, 2 para experiencia, 2 para alineación, 1 para educación requerida y 1 para otros criterios explícitos, excluyendo ubicación y modalidad

#### Scenario: Criterio no requerido o no aplicable
- **WHEN** la vacante no establece un requisito educativo ni existe otro criterio explícito del perfil que corresponda evaluar
- **THEN** el criterio aplicable recibe su máximo de puntos y queda marcado como `no_aplica`

#### Scenario: Falta evidencia en el CV
- **WHEN** el CV no aporta evidencia suficiente para un criterio aplicable
- **THEN** el criterio recibe cero puntos, queda marcado como `sin_evidencia` y el sistema distingue esa ausencia de una contradicción explícita

#### Scenario: Evidencia contradice un requisito
- **WHEN** la evidencia disponible contradice un criterio aplicable
- **THEN** el criterio recibe cero puntos y queda marcado como `contradicho` con evidencia que sustente la contradicción

#### Scenario: Ubicación ya validada
- **WHEN** el sistema calcula compatibilidad para una vacante que superó la elegibilidad de ubicación o modalidad
- **THEN** no añade ni resta puntos por ubicación o modalidad en la rúbrica

### Requirement: Puntaje final calculado por el sistema
El sistema SHALL calcular el puntaje final como la suma de los puntos por criterio menos las deducciones críticas configuradas, limitado al intervalo de 0.0 a 10.0 y con una cifra decimal.

#### Scenario: Suma válida
- **WHEN** el modelo devuelve puntajes válidos dentro de los límites de cada criterio
- **THEN** el puntaje guardado es la suma de los criterios menos las deducciones y se encuentra entre 0.0 y 10.0 con una cifra decimal

#### Scenario: Desglose inválido
- **WHEN** el modelo omite un criterio, devuelve puntos fuera de sus límites o un estado no admitido
- **THEN** el sistema rechaza el análisis como inválido y no guarda un puntaje parcial

#### Scenario: Puntaje o deducción inválidos
- **WHEN** un puntaje o deducción tiene más de una cifra decimal o excede los límites versionados
- **THEN** el sistema rechaza el análisis y no guarda un puntaje parcial

### Requirement: Conservar la versión de rúbrica aplicada
El sistema SHALL conservar en cada análisis la versión de configuración y rúbrica, además del desglose de criterios, requisitos críticos, deducciones y evidencia, para explicar el resultado.

#### Scenario: Análisis guardado
- **WHEN** un análisis se completa correctamente
- **THEN** queda asociada la versión exacta utilizada junto a sus criterios, puntajes, estados, requisitos críticos, deducciones y evidencia

### Requirement: Aplicar deducciones solo por requisitos críticos explícitos
El sistema SHALL aplicar deducciones configuradas únicamente por requisitos laborales explícitos, críticos para el cargo y directamente contradichos por evidencia del perfil.

#### Scenario: Administrador configura la deducción crítica
- **WHEN** una persona administradora versiona la rúbrica con un peso de deducción
- **THEN** el sistema guarda ese peso en la configuración y calcula la deducción sin dejar que el modelo elija su magnitud

#### Scenario: Requisito crítico contradicho con evidencia
- **WHEN** la publicación establece explícitamente un requisito laboral obligatorio y la evidencia del perfil lo contradice
- **THEN** el sistema aplica la deducción configurada y conserva el requisito, la evidencia y los puntos restados

#### Scenario: Requisito obligatorio sin evidencia
- **WHEN** la publicación establece un requisito obligatorio pero el perfil no permite confirmarlo ni contradecirlo
- **THEN** el sistema lo marca como pendiente de verificar y no resta puntos

#### Scenario: Requisito no explícito o ajeno al cargo
- **WHEN** una condición no es explícitamente obligatoria o no se relaciona con las funciones del cargo
- **THEN** el sistema no la clasifica como requisito crítico ni aplica una deducción

### Requirement: Excluir atributos personales de la compatibilidad
El sistema SHALL NOT otorgar ni restar puntos por discapacidad u otros atributos personales que no constituyan competencias o requisitos laborales relevantes para el cargo.

#### Scenario: El perfil o la publicación mencionan discapacidad
- **WHEN** el CV, el perfil o la publicación incluye información sobre discapacidad
- **THEN** el análisis la ignora al evaluar criterios, requisitos críticos y puntaje

#### Scenario: Se evalúa una competencia laboral
- **WHEN** la publicación exige una competencia relevante para las funciones
- **THEN** el sistema puede evaluarla con evidencia del perfil y solo deduce si la contradicción es explícita

### Requirement: Reutilizar la organización para una vacante y configuración
El sistema SHALL reutilizar una organización válida para la misma vacante, configuración y versión del contenido, evitando repetir esa etapa por cada perfil.

#### Scenario: Varios perfiles alcanzan su mínimo
- **WHEN** más de un perfil requiere organizar una misma vacante con la misma configuración y contenido
- **THEN** el sistema realiza una sola organización reutilizable para esos análisis

#### Scenario: Cambia la configuración o el contenido
- **WHEN** cambia la configuración de organización o el contenido relevante de la vacante
- **THEN** el sistema genera una nueva organización versionada sin reemplazar resultados históricos

### Requirement: Registrar consumo y duración de las etapas de IA
El sistema SHALL conservar por llamada de puntuación u organización la etapa, duración, resultado y tokens reportados por el proveedor, sin guardar prompts, CV ni respuestas completas.

#### Scenario: El proveedor informa tokens
- **WHEN** una llamada de IA informa tokens de entrada y salida
- **THEN** el sistema los conserva junto con la etapa, duración y resultado

#### Scenario: El proveedor no informa tokens
- **WHEN** una llamada termina sin datos de uso utilizables
- **THEN** el sistema registra los tokens como no disponibles

#### Scenario: Agregar telemetría
- **WHEN** se consultan métricas operativas de llamadas
- **THEN** pueden agruparse por etapa y resultado sin acceder a datos personales, prompts o respuestas completas

### Requirement: Reanalizar resultados vigentes con una nueva rúbrica
El sistema SHALL reprocesar en segundo plano los análisis vigentes cuando se introduzca una nueva escala y rúbrica, conservando los análisis anteriores para trazabilidad.

#### Scenario: Reprocesamiento de resultados existentes
- **WHEN** se activa el cambio a la nueva rúbrica
- **THEN** cada combinación vigente de perfil y vacante con análisis completo se programa para un nuevo análisis y el análisis previo permanece consultable

#### Scenario: Reprocesamiento aún pendiente
- **WHEN** el nuevo análisis de una combinación todavía no termina
- **THEN** el sistema conserva el resultado previo y no lo presenta como si hubiera sido calculado con la nueva rúbrica

### Requirement: Solicitar evidencia principal en la explicación del puntaje
El sistema SHALL solicitar al modelo solo las evidencias y razones principales necesarias para sustentar cada criterio, el puntaje y las deducciones, evitando explicaciones secundarias o repetidas sin imponer un límite de longitud.

#### Scenario: Evidencia breve sustenta un criterio
- **WHEN** una evidencia concreta basta para explicar el resultado de un criterio
- **THEN** la respuesta conserva esa evidencia de forma directa sin agregar contexto redundante ni una narración extensa

#### Scenario: Un criterio requiere varios elementos de evidencia
- **WHEN** más de un elemento es necesario para justificar el puntaje o una deducción
- **THEN** la respuesta conserva todos los elementos relevantes y omite detalles que no cambian la justificación

#### Scenario: No hay evidencia suficiente
- **WHEN** el CV no permite confirmar o contradecir un requisito
- **THEN** la respuesta conserva el estado de falta de evidencia sin inventar detalles para completar la explicación

#### Scenario: Se verifica el consumo de salida
- **WHEN** se compara la nueva instrucción con la versión anterior en una muestra representativa de análisis
- **THEN** el formato requerido sigue siendo válido y el consumo medio de tokens de salida disminuye sin pérdida de evidencia necesaria para puntuar
