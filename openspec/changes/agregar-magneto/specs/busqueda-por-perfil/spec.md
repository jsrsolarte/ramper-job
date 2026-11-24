# Spec Delta

## ADDED Requirements

### Requirement: Buscar en Magneto por preferencias efectivas
El sistema SHALL consultar Magneto con los términos y ubicaciones efectivos de cada grupo de búsqueda y procesar sus resultados por el flujo compartido.

#### Scenario: Perfiles con búsqueda equivalente
- **WHEN** varios perfiles tienen términos, ubicaciones y modalidad efectivos equivalentes
- **THEN** el sistema comparte la consulta a Magneto y evalúa cada resultado por separado para cada perfil elegible

#### Scenario: Primera página de resultados
- **WHEN** se consulta una combinación de término y ubicación
- **THEN** el sistema procesa como máximo la primera página de resultados de esa combinación

#### Scenario: Modalidad remota aceptada
- **WHEN** el grupo acepta vacantes remotas
- **THEN** el sistema incluye una consulta sin restricción de ciudad y aplica la elegibilidad de modalidad y ubicación con los datos disponibles

#### Scenario: Publicación ya conocida
- **WHEN** una búsqueda devuelve una publicación de Magneto ya registrada
- **THEN** el sistema reutiliza o actualiza su registro conforme a la identidad existente sin alterar seguimientos de los perfiles
