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

### Requirement: Preseleccionar vacantes automáticas por título
El sistema SHALL clasificar en lote los títulos de resultados automáticos frente a los términos compartidos de la solicitud de búsqueda, descartando únicamente incompatibilidades laborales claras.

#### Scenario: Consultar el embudo de una búsqueda
- **WHEN** una persona administradora revisa una consulta automática
- **THEN** el sistema muestra títulos recibidos, conservados y descartados por preselección, fichas solicitadas y recibidas, vacantes nuevas o conocidas, y análisis encolados y sus resultados finales
- **AND** las duraciones de la consulta y sus etapas se muestran en minutos
- **AND** no se muestran títulos, CV, prompts ni respuestas completas de la IA

#### Scenario: Un título tiene relación clara con la búsqueda
- **WHEN** el título de una vacante es compatible con los términos de búsqueda del grupo
- **THEN** el sistema conserva la vacante para consultar su ficha y continuar el análisis habitual

#### Scenario: Un título no tiene relación laboral clara
- **WHEN** el título de una vacante es manifiestamente ajeno a los términos y ocupaciones de la búsqueda
- **THEN** el sistema descarta esa vacante antes de consultar su ficha detallada y no programa análisis para ella

#### Scenario: El título es ambiguo o insuficiente
- **WHEN** el título no permite determinar con confianza si la vacante encaja
- **THEN** el sistema conserva la vacante para el flujo de análisis habitual

#### Scenario: Se preselecciona un grupo de solicitudes equivalentes
- **WHEN** varios perfiles comparten los mismos términos, ubicación y modalidad efectivos de búsqueda
- **THEN** el sistema ejecuta una clasificación común para sus resultados usando los términos compartidos, sin enviar los CV ni mezclar solicitudes distintas

#### Scenario: La IA no devuelve una clasificación válida
- **WHEN** la etapa de preselección falla, no está disponible o no clasifica un título recibido
- **THEN** el sistema conserva las vacantes afectadas y continúa con el flujo habitual

#### Scenario: Se registra una vacante manual desde una URL
- **WHEN** la persona administradora inicia el registro directo de una ficha pública
- **THEN** el sistema extrae y procesa esa ficha sin aplicar el filtro de títulos de resultados automáticos

### Requirement: Obtener detalles desde la ficha pública
El sistema SHALL consultar la ficha pública de cada resultado automático conservado por la preselección de títulos y extraer los datos disponibles además de los que aparecen en la tarjeta. Una vacante registrada directamente por URL SHALL continuar consultándose sin esa preselección.

#### Scenario: La ficha contiene más información que el listado
- **WHEN** una ficha pública incluye salario, ubicación o condiciones que no aparecen completos en el listado
- **THEN** el sistema conserva los valores de la ficha junto con el enlace original y la fuente

#### Scenario: La ficha contiene secciones estructuradas
- **WHEN** la ficha publica responsabilidades, requisitos, formación, experiencia, área, horario o número de vacantes
- **THEN** el sistema conserva cada dato en su campo correspondiente y no lo mezcla en un único texto de descripción

#### Scenario: Una vacante automática fue descartada por título
- **WHEN** la preselección clasifica claramente una vacante automática como ajena a la búsqueda
- **THEN** el sistema no consulta su ficha detallada

#### Scenario: Una vacante se registra directamente desde su URL
- **WHEN** la administración solicita procesar una ficha pública mediante su URL
- **THEN** el sistema consulta esa ficha y extrae sus datos disponibles sin preselección por título

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
El sistema SHALL permitir a la persona administradora iniciar una actualización de fuentes antes del siguiente ciclo periódico, usando el flujo de búsqueda, preselección conservadora por título, deduplicación y análisis elegible.

#### Scenario: Administración inicia una actualización antes del horario
- **WHEN** la persona administradora solicita actualizar fuentes antes de que venza el intervalo automático de 120 minutos
- **THEN** el sistema encola la actualización inmediatamente sin esperar al siguiente ciclo y conserva el horario periódico configurado

#### Scenario: La búsqueda encuentra una vacante nueva elegible
- **WHEN** la actualización manual encuentra una vacante que no está registrada, la preselección la conserva y cumple las condiciones del perfil
- **THEN** el sistema crea un único registro detallado y encola el análisis correspondiente

#### Scenario: La preselección considera dudoso un título
- **WHEN** la actualización manual encuentra un título que no permite descartar con confianza la vacante
- **THEN** el sistema la conserva y continúa con la extracción detallada y el análisis elegible

#### Scenario: La búsqueda encuentra una vacante ya analizada
- **WHEN** la actualización manual vuelve a encontrar una vacante que ya tiene registro y análisis completado
- **THEN** el sistema actualiza el mismo registro si corresponde y no crea otra vacante ni duplica el análisis por el solo hecho de repetir la búsqueda

#### Scenario: Ya hay una actualización periódica o manual en curso
- **WHEN** la persona administradora solicita una actualización mientras otra ejecución equivalente sigue activa
- **THEN** el sistema informa la ejecución existente y no inicia una búsqueda concurrente duplicada

### Requirement: Registrar una vacante administrativa usando solo su URL
El centro administrativo SHALL permitir iniciar el registro de una vacante pegando únicamente la URL pública de una publicación en un proveedor compatible.

#### Scenario: La persona administradora envía una URL pública compatible
- **WHEN** la persona administradora envía una URL válida de una ficha pública de El Empleo
- **THEN** el sistema identifica el proveedor y encola la extracción sin solicitar título, fuente ni otros datos manuales

#### Scenario: La URL no pertenece a un proveedor compatible
- **WHEN** la persona administradora envía una URL de un proveedor que no está habilitado
- **THEN** el sistema informa que el proveedor aún no es compatible y no consulta ni registra la publicación

#### Scenario: La URL no es pública o segura
- **WHEN** la URL no usa HTTPS, apunta a un host no permitido o requiere autenticación
- **THEN** el sistema la rechaza sin intentar acceder a recursos privados ni eludir controles de acceso

### Requirement: Extraer y normalizar los datos de la ficha pública
El sistema SHALL extraer de la URL compatible los datos públicos disponibles y normalizarlos al formato común de vacantes.

#### Scenario: La ficha contiene datos suficientes
- **WHEN** el proveedor devuelve una ficha pública interpretable con título y URL original
- **THEN** el sistema conserva los datos extraídos disponibles, fuente identificada y URL canónica

#### Scenario: La ficha no permite crear una vacante válida
- **WHEN** la ficha es inaccesible, está cerrada, no se puede interpretar o no contiene los datos mínimos requeridos
- **THEN** el sistema informa el resultado y no crea la vacante ni encola análisis

#### Scenario: El proveedor bloquea o limita la consulta
- **WHEN** el proveedor responde con bloqueo, límite de solicitudes o error temporal
- **THEN** el sistema detiene la extracción, informa que no fue posible completar el registro y no intenta evadir el control

### Requirement: Continuar por el flujo común de la vacante
Una vacante extraída desde una URL SHALL usar la deduplicación global y el flujo normal de evaluación independiente para cada perfil elegible.

#### Scenario: La URL ya corresponde a una publicación registrada
- **WHEN** la ficha extraída tiene una URL canónica que ya existe
- **THEN** el sistema reutiliza o actualiza la publicación existente sin crear un segundo registro global

#### Scenario: Se crea una vacante nueva desde la URL
- **WHEN** la ficha se extrae correctamente y no existe una publicación equivalente
- **THEN** el sistema guarda la publicación global y encola una evaluación individual para cada perfil activo elegible con CV y preferencias vigentes

#### Scenario: La publicación ya fue evaluada sin cambios materiales
- **WHEN** la URL corresponde a una publicación existente sin cambios materiales para el perfil, revisión y configuración vigentes
- **THEN** el sistema no duplica el análisis completado y muestra el estado del procesamiento administrativo

### Requirement: Registrar manualmente una vacante desde administración
El centro administrativo SHALL permitir que la persona administradora registre una vacante pegando únicamente la URL pública de una publicación admitida.

#### Scenario: La persona administradora envía una URL válida
- **WHEN** la persona administradora envía la URL HTTPS de una ficha pública compatible
- **THEN** el sistema encola su extracción, deduplicación y procesamiento y muestra el estado del registro

#### Scenario: La URL no corresponde a una ficha pública compatible
- **WHEN** la URL es inválida, no segura o pertenece a un proveedor no habilitado
- **THEN** el sistema rechaza el registro antes de encolar el procesamiento

#### Scenario: Una cuenta sin privilegios intenta registrar una vacante
- **WHEN** una cuenta aspirante solicita la pantalla o la acción de alta manual
- **THEN** el sistema deniega el acceso y no modifica vacantes ni inicia trabajos

### Requirement: Compartir la vacante manual entre perfiles elegibles
Una vacante registrada manualmente SHALL ser una publicación global y SHALL generar una evaluación independiente para cada perfil activo elegible con CV y preferencias vigentes.

#### Scenario: Se registra una vacante nueva
- **WHEN** la persona administradora registra una vacante activa que no estaba guardada
- **THEN** el sistema guarda una sola publicación y encola su análisis para cada perfil elegible según sus preferencias de ubicación y modalidad

#### Scenario: Los perfiles elegibles comparten la vacante
- **WHEN** dos o más perfiles son elegibles para la misma vacante manual
- **THEN** cada perfil recibe su propio puntaje y desglose conforme a su CV, preferencias, rúbrica y umbral vigentes

#### Scenario: Ningún perfil es elegible
- **WHEN** la vacante no cumple las preferencias geográficas o de modalidad de ningún perfil vigente
- **THEN** el sistema conserva la publicación global sin crear evaluaciones incompatibles

### Requirement: Evitar duplicar una vacante ingresada manualmente
El sistema SHALL reutilizar una publicación existente que tenga la misma URL pública canónica, sin importar si se encontró por una fuente automática o por el registro manual.

#### Scenario: La URL ya está registrada
- **WHEN** la persona administradora registra una vacante cuya URL canónica ya existe
- **THEN** el sistema actualiza o reutiliza la publicación existente y no crea un segundo registro global

#### Scenario: Se vuelve a registrar una vacante sin cambios materiales
- **WHEN** una vacante existente se registra manualmente de nuevo sin cambiar contenido material
- **THEN** el sistema no duplica análisis ya completados para el mismo perfil, revisión y configuración

### Requirement: Obtener vacantes públicas de Computrabajo Colombia
El sistema SHALL obtener publicaciones públicas de Computrabajo Colombia y normalizarlas al formato común, conservando la fuente y el enlace original.

#### Scenario: Tarjeta de una vacante disponible
- **WHEN** una consulta devuelve una tarjeta interpretable de Computrabajo
- **THEN** el sistema conserva el identificador externo, título, enlace y los datos disponibles de empresa, ubicación, salario y antigüedad

#### Scenario: Falta un dato en la tarjeta
- **WHEN** la tarjeta no informa un campo opcional
- **THEN** el sistema lo deja como desconocido sin inferirlo de la búsqueda

### Requirement: Enriquecer las publicaciones de Computrabajo
El sistema SHALL consultar la ficha pública de cada publicación única de Computrabajo y conservar los detalles disponibles sin perder los datos del listado.

#### Scenario: La ficha incluye condiciones y requisitos
- **WHEN** la ficha proporciona descripción, contrato, jornada, modalidad, formación o experiencia
- **THEN** el sistema conserva los datos disponibles en el formato común y mantiene los valores del listado cuando difieren

#### Scenario: La ficha no está disponible
- **WHEN** una ficha individual falla por un error temporal, vence el tiempo de espera o no se puede interpretar sin recibir una respuesta de bloqueo
- **THEN** el sistema conserva los datos del listado y continúa con las demás fichas de Computrabajo

### Requirement: Configurar el User-Agent de Computrabajo
El sistema SHALL permitir configurar el User-Agent utilizado en las consultas del listado y las fichas de Computrabajo, con un valor inicial compatible con el usado en la prueba compartida.

#### Scenario: Se cambia la configuración
- **WHEN** se configura un User-Agent distinto para Computrabajo
- **THEN** las siguientes solicitudes de esa fuente usan el valor configurado

### Requirement: Registrar fallos de Computrabajo
El sistema SHALL indicar la indisponibilidad de Computrabajo cuando una búsqueda o ficha sea bloqueada y SHALL permitir que las demás fuentes continúen.

#### Scenario: La fuente rechaza la búsqueda
- **WHEN** Computrabajo devuelve HTTP 403, 401 o 429 o exige autenticación para la búsqueda pública
- **THEN** el sistema detiene las siguientes solicitudes a Computrabajo en esa ejecución, registra la fuente como no disponible y no intenta evadir el control

#### Scenario: Una ficha bloquea las consultas de la fuente
- **WHEN** una ficha de Computrabajo responde HTTP 401, 403 o 429 durante una ejecución
- **THEN** el sistema conserva los datos de listado obtenidos, detiene las siguientes solicitudes a Computrabajo en esa ejecución y registra la fuente como no disponible

#### Scenario: Falla una fuente y otra responde
- **WHEN** Computrabajo no está disponible y El Empleo responde normalmente
- **THEN** el sistema conserva y procesa los resultados de El Empleo

### Requirement: Deduplicar publicaciones de Computrabajo
El sistema SHALL identificar cada publicación de Computrabajo por su identificador externo cuando esté disponible y reutilizar el flujo común de deduplicación y análisis por perfil.

#### Scenario: Una publicación aparece en varias búsquedas
- **WHEN** dos consultas devuelven la misma publicación de Computrabajo con el mismo identificador
- **THEN** el sistema conserva un único registro de esa fuente y mantiene los seguimientos y análisis existentes por perfil
