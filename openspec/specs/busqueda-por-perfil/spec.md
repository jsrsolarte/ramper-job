# Búsqueda por perfil Specification

## Purpose

Encuentra vacantes a partir de los cargos y habilidades relevantes para cada perfil y conecta esas búsquedas con el flujo común de ingesta y análisis privado.

## Requirements

### Requirement: Derivar palabras clave desde cada perfil
El sistema SHALL generar con la configuración de IA vigente un conjunto acotado de palabras clave laborales usando el CV y las preferencias de la revisión vigente.

#### Scenario: Perfil con CV y preferencias vigentes
- **WHEN** se inicia una actualización para un perfil activo
- **THEN** el modelo devuelve palabras clave relacionadas con cargos, habilidades o sectores respaldados por el CV y las preferencias

#### Scenario: OmniRoute no está disponible
- **WHEN** no se puede generar el conjunto de palabras clave
- **THEN** el sistema registra el fallo para reintento, conserva los resultados guardados y no inicia una búsqueda general sin relación con el perfil

### Requirement: Ajustar la generación de palabras clave
El administrador SHALL poder ajustar y versionar el prompt que genera palabras clave, y el sistema SHALL usar la versión activa en las nuevas búsquedas.

#### Scenario: Se activa una nueva versión del prompt
- **WHEN** el administrador guarda una nueva configuración de búsqueda
- **THEN** la siguiente actualización usa esa versión para generar términos

### Requirement: Buscar vacantes con términos y ubicaciones del perfil
Cada conector compatible SHALL recibir las palabras clave, ubicaciones y modalidad aplicables a una solicitud de búsqueda y devolver las vacantes públicas encontradas, conservando la URL original. El sistema SHALL compartir una consulta entre perfiles cuando esos criterios efectivos sean equivalentes. SHALL completar el conjunto de búsquedas mediante unidades de trabajo acotadas y reanudables, sin omitir combinaciones por exceder el límite de una tarea.

#### Scenario: Elempleo recibe una búsqueda específica
- **WHEN** el conjunto contiene el término «procesos» y una ubicación aplicable
- **THEN** el conector consulta la búsqueda pública de Elempleo combinando el término y el filtro geográfico

#### Scenario: Dos perfiles tienen criterios de búsqueda equivalentes
- **WHEN** dos perfiles vigentes generan las mismas palabras clave, ubicaciones aplicables y modalidad remota para una fuente
- **THEN** el sistema realiza una sola consulta equivalente a esa fuente y asocia cada vacante encontrada con ambos perfiles

#### Scenario: Perfiles distintos requieren consultas distintas
- **WHEN** las palabras clave, ubicaciones aplicables o modalidad remota difieren entre dos perfiles
- **THEN** el sistema conserva solicitudes de búsqueda separadas para los criterios que difieren

#### Scenario: Varias consultas encuentran la misma vacante
- **WHEN** más de una consulta devuelve la misma publicación
- **THEN** el sistema conserva una sola vacante y evita duplicar su análisis para el mismo perfil, incluso tras cambiar la revisión

#### Scenario: Un perfil genera más trabajo que el límite de una tarea
- **WHEN** las combinaciones de términos, ubicaciones y fichas de una fuente exceden el presupuesto de trabajo de una tarea Celery
- **THEN** el sistema procesa unidades acotadas hasta cubrir todas las combinaciones, sin mantener una sola tarea activa más allá de su límite

#### Scenario: Se reintenta una unidad interrumpida
- **WHEN** una unidad de búsqueda vence o se interrumpe después de guardar parte de sus resultados
- **THEN** el sistema reanuda desde el último punto confirmado y no duplica vacantes, asociaciones, seguimientos ni análisis

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

### Requirement: Compartir vacantes sin mezclar resultados privados
El sistema SHALL reutilizar una vacante normalizada encontrada por cualquier búsqueda y mantener el análisis independiente para cada perfil activo relacionado con la búsqueda.

#### Scenario: Una publicación coincide con búsquedas de dos perfiles
- **WHEN** una misma vacante aparece en una búsqueda compartida o en consultas distintas de dos perfiles
- **THEN** se conserva una publicación y cada perfil relacionado recibe su propio análisis privado en su dashboard

#### Scenario: Los perfiles tienen rúbricas o decisiones distintas
- **WHEN** dos perfiles comparten una vacante encontrada mediante criterios de búsqueda equivalentes
- **THEN** el sistema evalúa por separado la vacante con la rúbrica vigente de cada perfil y conserva sus estados de seguimiento de forma independiente

### Requirement: Respetar la pausa individual en las búsquedas automáticas
El sistema SHALL iniciar búsquedas automáticas y asociar sus resultados únicamente con perfiles que tengan habilitada la búsqueda.

#### Scenario: Se ejecuta un ciclo periódico
- **WHEN** comienza un ciclo automático de búsqueda con perfiles habilitados y pausados
- **THEN** el sistema consulta fuentes solo para perfiles habilitados

#### Scenario: Administración fuerza una actualización de fuentes
- **WHEN** la persona administradora inicia una búsqueda manual de fuentes mientras hay perfiles pausados
- **THEN** el sistema incluye únicamente los perfiles con búsqueda habilitada y conserva pausados los demás

#### Scenario: Hay una actualización de perfil en cola al pausarlo
- **WHEN** una tarea de búsqueda de un perfil pausado está en cola y todavía no inició
- **THEN** el sistema omite esa búsqueda sin consultar fuentes ni volver a encolarla

#### Scenario: Una búsqueda compartida coincide con un perfil pausado
- **WHEN** una consulta equivalente corresponde a perfiles habilitados y a otro perfil pausado
- **THEN** el sistema ejecuta una sola consulta para los perfiles habilitados y no asocia el resultado ni encola análisis de esa búsqueda para el perfil pausado

#### Scenario: Se pausa un perfil durante una búsqueda compartida
- **WHEN** la consulta ya comenzó para un grupo y uno de sus perfiles se pausa antes de asociar los resultados
- **THEN** el sistema puede completar la consulta para los perfiles habilitados, pero excluye al perfil pausado de nuevos resultados y análisis originados por esa búsqueda

#### Scenario: Se reanuda la búsqueda del perfil
- **WHEN** una persona habilita de nuevo la búsqueda de su perfil
- **THEN** el perfil participa desde el siguiente ciclo automático normal sin iniciar una consulta inmediata ni recuperar tareas omitidas

#### Scenario: Se procesan vacantes existentes o ingresadas manualmente
- **WHEN** un perfil tiene pausada la búsqueda automática y se analiza una vacante ya guardada o registrada manualmente por administración
- **THEN** el sistema mantiene el análisis y acceso a esa vacante según el flujo común del perfil

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
