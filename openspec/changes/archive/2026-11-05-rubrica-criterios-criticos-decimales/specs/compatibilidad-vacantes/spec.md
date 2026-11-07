# Spec Delta

## MODIFIED Requirements

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
