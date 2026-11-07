# Spec Delta

## MODIFIED Requirements

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
