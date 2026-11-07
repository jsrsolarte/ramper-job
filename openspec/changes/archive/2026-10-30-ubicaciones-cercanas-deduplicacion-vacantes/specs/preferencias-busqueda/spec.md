# Spec Delta

## Purpose

Permite mantener preferencias de búsqueda claras y comparar ciudades seleccionadas con ubicaciones laborales cercanas de manera consistente en el sistema.

## ADDED Requirements

### Requirement: Mostrar preferencias como listas editables
El sistema SHALL presentar las frases y ubicaciones del perfil como listas verticales con controles para agregar y quitar elementos.

#### Scenario: Editar frases y ubicaciones
- **WHEN** el usuario abre la edición de su perfil
- **THEN** cada frase y ubicación vigente aparece en una fila independiente y puede quitarse o ampliarse desde el mismo control

### Requirement: Buscar y evaluar en ubicaciones cercanas
El sistema SHALL convertir cada ubicación preferida en consultas geográficas compatibles con la bolsa y evaluar resultados respecto a la ubicación elegida y sus equivalencias cercanas configuradas.

#### Scenario: Elempleo filtra por Soacha
- **WHEN** el perfil busca una frase de empleo en Soacha
- **THEN** Elempleo recibe una consulta de la frase combinada con el filtro de ciudad de Soacha y devuelve resultados de esa búsqueda

#### Scenario: Búsqueda en el Valle de Aburrá
- **WHEN** el perfil selecciona Medellín y el grupo cercano configurado
- **THEN** el sistema consulta Elempleo para Medellín y los municipios incluidos en ese grupo y consolida los resultados en una lista

#### Scenario: Bogotá y municipios cercanos
- **WHEN** el perfil selecciona Bogotá
- **THEN** el sistema usa el filtro de ubicación disponible en Elempleo para Bogotá y sus alrededores, y considera Soacha y otras ubicaciones configuradas al evaluar compatibilidad

#### Scenario: La bolsa limita ciudades por consulta
- **WHEN** la bolsa permite filtrar como máximo tres ciudades en una consulta
- **THEN** el sistema divide las ubicaciones expandidas en consultas válidas y combina los resultados

#### Scenario: Ubicación sin área configurada
- **WHEN** el perfil selecciona una ubicación sin grupo de cercanía definido
- **THEN** el sistema conserva la comparación literal de esa ubicación

### Requirement: Priorizar vacantes recién publicadas
El sistema SHALL priorizar vacantes publicadas dentro de una ventana de recencia de 24 horas cuando la fuente provea hora de publicación, y usar el filtro reciente más cercano que exponga la bolsa cuando no provea una hora exacta.

#### Scenario: Fuente publica hora exacta
- **WHEN** una vacante incluye fecha y hora de publicación verificables
- **THEN** el sistema solo la considera dentro de la ventana prioritaria si fue publicada durante las últimas 24 horas

#### Scenario: Elempleo expone una categoría de recencia
- **WHEN** Elempleo no provee una hora exacta y ofrece «Hoy y ayer»
- **THEN** el sistema aplica esa categoría y conserva su etiqueta de recencia en los datos de la vacante sin afirmar que equivale exactamente a 24 horas
