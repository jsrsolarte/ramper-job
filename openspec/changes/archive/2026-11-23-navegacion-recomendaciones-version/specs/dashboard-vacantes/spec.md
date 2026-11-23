# Spec Delta

## MODIFIED Requirements

### Requirement: Navegar entre vacantes recomendadas y pendientes de análisis
El dashboard SHALL presentar las vacantes por analizar y las recomendaciones como pestañas de la experiencia privada de vacantes. La navegación principal de las personas aspirantes SHALL ofrecer enlaces directos a «Recomendaciones», «Mi perfil» y «Análisis», con «Análisis» como pantalla independiente.

#### Scenario: La persona abre la pestaña de análisis pendiente
- **WHEN** la persona selecciona la pestaña «Por analizar»
- **THEN** el sistema muestra las vacantes pendientes del perfil actual sin cambiar el estado técnico de ningún análisis

#### Scenario: La persona abre la pestaña de recomendaciones
- **WHEN** la persona selecciona la pestaña «Recomendaciones»
- **THEN** el sistema muestra las recomendaciones disponibles del perfil actual sin alterar los análisis pendientes

#### Scenario: La persona abre Análisis desde la navegación principal
- **WHEN** la persona selecciona «Análisis» junto a «Mi perfil»
- **THEN** el sistema muestra las métricas de puntaje de su perfil sin alterar análisis ni estados de seguimiento

#### Scenario: La persona vuelve a Recomendaciones desde otra pantalla
- **WHEN** una persona aspirante selecciona «Recomendaciones» en la navegación principal
- **THEN** el sistema abre las recomendaciones de su perfil y el enlace identifica esa pantalla como activa
