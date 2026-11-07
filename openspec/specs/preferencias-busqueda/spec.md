# Preferencias de búsqueda Specification

## Purpose

Permite mantener preferencias de búsqueda claras y comparar ubicaciones seleccionadas con municipios cercanos configurados.

## Requirements

### Requirement: Mostrar preferencias como listas editables
El sistema SHALL presentar las frases y ubicaciones del perfil como listas verticales con controles para agregar y quitar elementos.

#### Scenario: Editar frases y ubicaciones
- **WHEN** el usuario abre la edición de su perfil
- **THEN** cada frase y ubicación vigente aparece en una fila independiente y puede quitarse o ampliarse desde el mismo control

### Requirement: Buscar y evaluar en ubicaciones cercanas
El sistema SHALL convertir cada ubicación preferida en consultas geográficas compatibles con la bolsa y evaluar resultados respecto a la ubicación y sus equivalencias cercanas configuradas.

#### Scenario: Elempleo filtra por Soacha
- **WHEN** el perfil busca una frase de empleo en Soacha
- **THEN** Elempleo recibe una consulta de la frase combinada con el filtro de ciudad de Soacha

#### Scenario: Búsqueda en el Valle de Aburrá
- **WHEN** el perfil selecciona Medellín y su grupo cercano configurado
- **THEN** el sistema consulta Elempleo para Medellín y los municipios del grupo, y consolida los resultados

#### Scenario: Bogotá y municipios cercanos
- **WHEN** el perfil selecciona Bogotá
- **THEN** el sistema usa los filtros de Bogotá y ubicaciones cercanas configuradas al buscar y evaluar compatibilidad

#### Scenario: La bolsa limita ciudades por consulta
- **WHEN** la bolsa limita el número de ciudades por consulta
- **THEN** el sistema divide las ubicaciones expandidas en consultas válidas y combina los resultados

#### Scenario: Ubicación sin área configurada
- **WHEN** el perfil selecciona una ubicación sin grupo cercano definido
- **THEN** el sistema conserva la comparación literal de esa ubicación

### Requirement: Priorizar vacantes recién publicadas
El sistema SHALL priorizar vacantes de las últimas 24 horas cuando la fuente entregue hora exacta y aplicar la categoría reciente más cercana que ofrezca la fuente cuando no la entregue.

#### Scenario: Fuente publica hora exacta
- **WHEN** una vacante incluye fecha y hora de publicación verificables
- **THEN** el sistema considera prioritaria la vacante si fue publicada durante las últimas 24 horas

#### Scenario: Elempleo expone una categoría de recencia
- **WHEN** Elempleo no provee una hora exacta y ofrece «Hoy y ayer»
- **THEN** el sistema aplica esa categoría y conserva su etiqueta sin afirmar que equivale exactamente a 24 horas
