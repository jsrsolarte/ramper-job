# Ingesta de vacantes

## Purpose

Obtener y normalizar vacantes desde sus fichas públicas para que los resultados reflejen las condiciones publicadas y las preferencias de búsqueda del aspirante.

## Requirements

### Requirement: Scraping de vacantes públicas
El sistema SHALL obtener vacantes mediante scraping de páginas públicas de elempleo.com Colombia, sin acceder a áreas que requieran autenticación ni evadir controles de acceso o medidas de seguridad.

#### Scenario: Página pública disponible
- **WHEN** una página pública de elempleo.com contiene vacantes
- **THEN** el sistema obtiene vacantes públicas y conserva el enlace a cada publicación original

#### Scenario: La fuente bloquea la consulta pública
- **WHEN** elempleo.com bloquea la consulta o solicita autenticación
- **THEN** el sistema detiene la extracción de esa página y deja visible que la fuente no está disponible

### Requirement: Conectores de fuentes intercambiables
El sistema SHALL integrar cada bolsa de empleo mediante un conector común para añadir fuentes sin cambiar el flujo compartido de análisis y presentación.

#### Scenario: Se agrega una nueva bolsa de empleo
- **WHEN** se habilita un conector que cumple el contrato común de fuente
- **THEN** sus vacantes normalizadas pasan al mismo flujo de deduplicación, análisis y presentación

### Requirement: Normalizar vacantes de distintas fuentes
El sistema SHALL conservar en una estructura común los datos disponibles de cada vacante, incluidos la fuente y el enlace original.

#### Scenario: Vacante con campos incompletos
- **WHEN** una vacante no incluye alguno de los campos esperados
- **THEN** el sistema conserva los campos disponibles y deja los datos faltantes como desconocidos

### Requirement: Actualizar publicaciones ya conocidas
El sistema SHALL actualizar una vacante conocida de una fuente en lugar de crear una segunda publicación visible, y SHALL conservar los seguimientos existentes por perfil al actualizar la publicación.

#### Scenario: La fuente devuelve una publicación ya registrada
- **WHEN** una consulta encuentra una vacante que ya está registrada para esa fuente
- **THEN** el sistema actualiza sus datos disponibles y mantiene un solo registro visible

#### Scenario: La publicación está descartada para un perfil
- **WHEN** una consulta vuelve a encontrar una publicación cuyo seguimiento está descartado para un perfil
- **THEN** el sistema actualiza la vacante compartida sin crear otro seguimiento ni cambiar el estado descartado de ese perfil

#### Scenario: La misma publicación tiene estados distintos por perfil
- **WHEN** la publicación se actualiza y distintos perfiles tienen seguimientos diferentes
- **THEN** el sistema conserva el estado de cada perfil de forma independiente

### Requirement: Obtener detalles desde la ficha pública
El sistema SHALL consultar la ficha pública de cada vacante única encontrada y extraer los datos disponibles además de los que aparecen en la tarjeta de resultados.

#### Scenario: La ficha contiene más información que el listado
- **WHEN** una ficha pública incluye salario, ubicación o condiciones que no aparecen completos en el listado
- **THEN** el sistema conserva los valores de la ficha junto con el enlace original y la fuente

#### Scenario: La ficha contiene secciones estructuradas
- **WHEN** la ficha publica responsabilidades, requisitos, formación, experiencia, área, horario o número de vacantes
- **THEN** el sistema conserva cada dato en su campo correspondiente y no lo mezcla en un único texto de descripción

### Requirement: Normalizar condiciones y ubicación de la vacante
El sistema SHALL conservar por separado el salario publicado, la ciudad, la dirección o zona, la modalidad y el tipo de contrato cuando esos datos estén disponibles.

#### Scenario: Salario detallado y rango del listado
- **WHEN** el listado muestra un rango salarial y la ficha indica un valor exacto y su periodicidad
- **THEN** el sistema conserva tanto el rango como el valor exacto y la periodicidad sin sustituir uno por otro

#### Scenario: Ubicación presencial explícita
- **WHEN** la ficha indica ciudad, dirección y modalidad presencial
- **THEN** el sistema conserva la ciudad y la dirección por separado y clasifica la modalidad como presencial

#### Scenario: La ficha no informa un campo
- **WHEN** no se encuentra un dato en la ficha ni en el listado
- **THEN** el sistema lo deja como desconocido y no lo infiere de la ciudad usada para buscar

### Requirement: Respetar la ubicación preferida al recomendar vacantes
El sistema SHALL comparar la ubicación obtenida de la ficha con las ubicaciones preferidas y sus equivalencias cercanas configuradas antes de crear un análisis para el perfil.

#### Scenario: Ficha en una ciudad fuera de las preferencias
- **WHEN** el perfil acepta Medellín y Envigado, pero la ficha indica Bogotá como ubicación presencial
- **THEN** el sistema no crea un análisis ni presenta esa vacante como recomendación para ese perfil

#### Scenario: Ficha en un municipio cercano aceptado
- **WHEN** la ubicación de la ficha pertenece a un área cercana expandida desde una ubicación preferida
- **THEN** el sistema conserva la vacante para su análisis y recomendación

#### Scenario: Vacante remota
- **WHEN** la ficha indica que el trabajo es remoto
- **THEN** el sistema solo la conserva para análisis si el perfil acepta vacantes remotas

#### Scenario: Ubicación sin determinar
- **WHEN** la ficha y el listado no permiten determinar la ubicación real
- **THEN** el sistema marca la ubicación como no informada y no asigna como real la ciudad de la consulta

### Requirement: Mantener resultados parciales ante fallos en fichas
El sistema SHALL conservar los datos obtenidos del listado cuando no pueda consultar una ficha individual y continuar procesando las demás vacantes de la búsqueda.

#### Scenario: Ficha individual inaccesible
- **WHEN** una ficha devuelve un error, vence el tiempo de espera o no puede analizarse
- **THEN** el sistema mantiene los campos disponibles del listado, deja vacíos los detalles desconocidos y continúa con las otras vacantes

### Requirement: Presentar condiciones estructuradas de la vacante
El sistema SHALL mostrar en el dashboard la ubicación y las condiciones disponibles de la ficha, y no presentará la descripción completa de la vacante como contenido de la tarjeta.

#### Scenario: Ver vacante con detalles extraídos
- **WHEN** una recomendación tiene salario, ciudad, modalidad o contrato extraídos de la ficha
- **THEN** el dashboard muestra esos datos con etiquetas claras y omite los campos que estén vacíos

### Requirement: Conservar categorías de IA y mostrar palabras clave concisas
El sistema SHALL guardar en la base de datos las categorías estructuradas que devuelva el modelo, incluidas hasta cinco palabras clave extraídas de la descripción de la vacante, y SHALL mostrar esas palabras clave de forma concisa en el dashboard.

#### Scenario: La descripción permite extraer palabras clave
- **WHEN** el modelo organiza una vacante cuya descripción contiene habilidades o temas laborales concretos
- **THEN** el sistema persiste las palabras clave y demás categorías devueltas, y muestra las palabras clave en la tarjeta sin desplegar la descripción completa

#### Scenario: El modelo devuelve categorías adicionales
- **WHEN** el modelo devuelve responsabilidades, requisitos o condiciones organizadas
- **THEN** el sistema conserva esas categorías en la base de datos aunque la tarjeta muestre solo las palabras clave

### Requirement: Permitir una actualización manual de fuentes
El sistema SHALL permitir a la persona administradora iniciar una actualización de fuentes antes del siguiente ciclo periódico, usando el flujo habitual de búsqueda, deduplicación y análisis elegible.

#### Scenario: Administración inicia una actualización antes del horario
- **WHEN** la persona administradora solicita actualizar fuentes antes de que venza el intervalo automático de 120 minutos
- **THEN** el sistema encola la actualización inmediatamente sin esperar al siguiente ciclo y conserva el horario periódico configurado

#### Scenario: La búsqueda encuentra una vacante nueva elegible
- **WHEN** la actualización manual encuentra una vacante que no está registrada y cumple las condiciones del perfil
- **THEN** el sistema crea un único registro y encola el análisis correspondiente

#### Scenario: La búsqueda encuentra una vacante ya analizada
- **WHEN** la actualización manual vuelve a encontrar una vacante que ya tiene registro y análisis completado
- **THEN** el sistema actualiza el mismo registro si corresponde y no crea otra vacante ni duplica el análisis por el solo hecho de repetir la búsqueda

#### Scenario: Ya hay una actualización periódica o manual en curso
- **WHEN** la persona administradora solicita una actualización mientras otra ejecución equivalente sigue activa
- **THEN** el sistema informa la ejecución existente y no inicia una búsqueda concurrente duplicada
