# Spec Delta

## Purpose

Permite a la administración conocer incidentes operativos recurrentes o falta de progreso mediante avisos agrupados y limitados.

## ADDED Requirements

### Requirement: Detectar errores recurrentes
El sistema SHALL abrir un incidente cuando ocurran al menos tres fallos de la misma categoría y componente o fuente en una ventana de 30 minutos, usando categorías seguras y sin contar relecturas del mismo evento.

#### Scenario: Una fuente falla repetidamente
- **WHEN** se registran tres fallos distintos de la misma fuente y categoría durante 30 minutos
- **THEN** se abre o actualiza un incidente agrupado con su cantidad y periodo observado

#### Scenario: Ocurre un fallo aislado
- **WHEN** una categoría no alcanza el umbral de recurrencia
- **THEN** no se abre un incidente de error recurrente por ese único fallo

### Requirement: Detectar trabajo sin progreso
El sistema SHALL abrir un incidente si existe trabajo elegible pendiente o en ejecución sin progreso confirmado durante 30 minutos fuera de pausas aplicables.

#### Scenario: Hay trabajo detenido
- **WHEN** una unidad elegible permanece sin progreso confirmado durante 30 minutos y no está cubierta por una pausa
- **THEN** administración ve un incidente de trabajo sin progreso con el tiempo y tipo de trabajo afectados

#### Scenario: No hay trabajo pendiente
- **WHEN** no existe trabajo elegible para procesar
- **THEN** la falta de actividad no se interpreta como fallo

#### Scenario: Existe una pausa autorizada
- **WHEN** una pausa global, individual o franja automática impide legítimamente ejecutar el trabajo correspondiente
- **THEN** ese tiempo no genera una alerta de falta de progreso por el trabajo pausado

### Requirement: Detectar retraso del ciclo automático
El sistema SHALL señalar un incidente cuando un ciclo automático global siga vencido 30 minutos después de su hora estimada y no se haya registrado su inicio, excluyendo pausas programadas y globales.

#### Scenario: El ciclo está retrasado
- **WHEN** el ciclo sigue sin inicio confirmado 30 minutos después de su vencimiento en horario permitido
- **THEN** administración ve una alerta de ciclo retrasado y su hora estimada anterior

#### Scenario: Se está en franja de pausa
- **WHEN** la hora estimada cae dentro de la franja de pausa automática
- **THEN** el plazo de retraso comienza a contar desde la siguiente hora permitida, no durante la pausa

### Requirement: Presentar incidentes a administración
El centro administrativo SHALL mostrar incidentes activos y recientes, categoría, componente, primera y última observación, cantidad, estado y enlace a observabilidad cuando corresponda.

#### Scenario: Se revisa un incidente
- **WHEN** una cuenta administradora abre el centro
- **THEN** puede distinguir incidentes activos, recuperados y reconocidos y consultar evidencia agregada sin datos privados

#### Scenario: La condición se recupera
- **WHEN** se confirma que una condición activa dejó de cumplirse durante dos comprobaciones consecutivas
- **THEN** se marca recuperada y se conserva su historial

#### Scenario: Administración reconoce el incidente
- **WHEN** la persona administradora marca un incidente como revisado
- **THEN** queda reconocido sin considerarlo resuelto mientras persista la condición

#### Scenario: Una cuenta no administrativa consulta alertas
- **WHEN** una cuenta sin privilegios administrativos solicita alertas o sus datos
- **THEN** el sistema deniega el acceso sin revelar información operativa

### Requirement: Notificar al dispositivo sin saturar
El sistema SHALL ofrecer notificaciones operativas por dispositivo con consentimiento explícito y desactivadas por defecto, agrupando incidentes y limitando a un aviso cada seis horas por dispositivo.

#### Scenario: Aparece un incidente
- **WHEN** hay incidentes nuevos para una cuenta administradora con un dispositivo habilitado y no se ha enviado un aviso en las seis horas anteriores
- **THEN** se intenta un único aviso genérico que dirige al centro administrativo

#### Scenario: Se repite un incidente o surgen otros durante el intervalo
- **WHEN** hay nuevos eventos antes de transcurrir seis horas desde el último aviso
- **THEN** se actualiza el centro administrativo sin enviar otro aviso inmediato y se agrupan incidentes nuevos aún activos para el siguiente aviso permitido

#### Scenario: El incidente se recupera antes del siguiente aviso
- **WHEN** un incidente se recupera antes de que corresponda la siguiente notificación agrupada
- **THEN** no genera un aviso diferido por sí solo y permanece en el historial administrativo

#### Scenario: Se desactiva el canal o se niega permiso
- **WHEN** el administrador desactiva las notificaciones o el dispositivo no concede permiso
- **THEN** no se envían avisos a ese dispositivo y el centro administrativo sigue mostrando incidentes

### Requirement: Proteger la información y limitar garantías
Las alertas SHALL usar datos agregados y categorías controladas, sin CV, consultas, credenciales ni detalles de vacantes, y SHALL informar las limitaciones del mecanismo de vigilancia y entrega.

#### Scenario: El servicio de alertas deja de funcionar
- **WHEN** no hay señales suficientes para comprobar la salud del procesamiento o la vigilancia
- **THEN** el centro informa que el estado no se puede verificar cuando vuelve a estar accesible y no presenta la ausencia de alerta como prueba de salud

#### Scenario: Se pulsa una notificación
- **WHEN** una persona abre una alerta desde el dispositivo
- **THEN** se aplican la autenticación y autorización administrativas habituales antes de mostrar información operativa
