## ADDED Requirements

### Requirement: Buscar en Computrabajo por perfil
El sistema SHALL consultar Computrabajo Colombia con los términos y ubicaciones aplicables del perfil y reutilizar las consultas equivalentes entre perfiles.

#### Scenario: Búsqueda por término y ciudad
- **WHEN** un perfil solicita «analista de procesos» para Medellín
- **THEN** el sistema consulta la búsqueda pública correspondiente de Computrabajo con ese término y ciudad

#### Scenario: Ubicaciones cercanas
- **WHEN** una ubicación del perfil tiene municipios cercanos configurados
- **THEN** el sistema consulta las ubicaciones aplicables y consolida sus resultados sin duplicar publicaciones

#### Scenario: Preferencia remota
- **WHEN** el perfil acepta vacantes remotas
- **THEN** el sistema aplica las reglas comunes de elegibilidad para vacantes remotas sin atribuirles una ciudad inferida de la consulta

### Requirement: Limitar y ordenar la búsqueda en Computrabajo
Cada consulta a Computrabajo SHALL solicitar exclusivamente la primera página de resultados, con el filtro de la fuente `pubdate=1` y orden `by=relevance`.

#### Scenario: Se genera la URL de búsqueda
- **WHEN** el sistema busca un término y una ubicación en Computrabajo
- **THEN** la solicitud usa la ruta pública por término y ciudad, incluye `pubdate=1`, `p=1` y `by=relevance`, y no solicita páginas posteriores

#### Scenario: Se busca un término compuesto en una ciudad
- **WHEN** el sistema consulta «analista de procesos» en Medellín
- **THEN** usa una URL como `https://www.computrabajo.com.co/trabajo-de-analista-de-procesos-en-medellin?pubdate=1&p=1&by=relevance`, normalizando acentos y espacios en la ruta

#### Scenario: La fuente muestra una fecha relativa de ayer
- **WHEN** un resultado de la primera página filtrada muestra la etiqueta «Ayer»
- **THEN** el sistema conserva la etiqueta y no lo descarta solo por esa etiqueta
