# Spec Delta

## MODIFIED Requirements

### Requirement: Obtener detalles desde la ficha pública
El sistema SHALL reutilizar la ficha previamente descargada de un resultado automático conocido por URL normalizada y consultar la ficha cuando no exista detalle confirmado. Una vacante registrada directamente por URL SHALL continuar consultándose sin esa preselección.

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
- **THEN** el sistema reutiliza el detalle confirmado si existe o consulta la ficha si no existe, sin preselección por título

#### Scenario: La ficha ya fue descargada
- **WHEN** el listado contiene una URL normalizada con detalle confirmado para esa fuente
- **THEN** el sistema reutiliza el detalle sin volver a solicitarlo y continúa asociando la vacante a los perfiles elegibles

#### Scenario: Una consulta anterior de detalle falló
- **WHEN** existe una publicación sin evidencia confiable de descarga de ficha exitosa
- **THEN** el sistema intenta obtener el detalle y no considera su sola presencia como ficha descargada

### Requirement: Enriquecer las publicaciones de Computrabajo
El sistema SHALL consultar la ficha pública de cada publicación de Computrabajo sin detalle confirmado y reutilizar el detalle ya obtenido por URL normalizada y conservar los detalles disponibles sin perder los datos del listado.

#### Scenario: La ficha incluye condiciones y requisitos
- **WHEN** la ficha proporciona descripción, contrato, jornada, modalidad, formación o experiencia
- **THEN** el sistema conserva los datos disponibles en el formato común y mantiene los valores del listado cuando difieren

#### Scenario: La ficha no está disponible
- **WHEN** una ficha individual falla por un error temporal, vence el tiempo de espera o no se puede interpretar sin recibir una respuesta de bloqueo
- **THEN** el sistema conserva los datos del listado y continúa con las demás fichas de Computrabajo

### Requirement: Deduplicar publicaciones de Computrabajo
El sistema SHALL identificar cada publicación de Computrabajo por su URL de ficha normalizada sin parámetros ni fragmento y reutilizar el flujo común de deduplicación y análisis por perfil.

#### Scenario: Una publicación aparece en varias búsquedas
- **WHEN** dos consultas devuelven la misma publicación de Computrabajo con la misma URL normalizada
- **THEN** el sistema conserva un único registro de esa fuente y mantiene los seguimientos y análisis existentes por perfil

### Requirement: Continuar por el flujo común de la vacante
Una vacante extraída desde una URL SHALL usar la deduplicación global y el flujo normal de evaluación independiente para cada perfil elegible.

#### Scenario: La URL ya corresponde a una publicación registrada
- **WHEN** la ficha extraída tiene una URL canónica que ya existe
- **THEN** el sistema reutiliza o actualiza la publicación existente sin crear un segundo registro global

#### Scenario: Se crea una vacante nueva desde la URL
- **WHEN** la ficha se extrae correctamente y no existe una publicación equivalente
- **THEN** el sistema guarda la publicación global y encola una evaluación individual para cada perfil activo elegible con CV y preferencias vigentes

#### Scenario: La publicación ya fue evaluada sin cambios materiales
- **WHEN** la URL corresponde a una publicación existente con un análisis completado para el perfil
- **THEN** el sistema reutiliza el análisis completado sin reevaluar y muestra el estado del procesamiento administrativo

### Requirement: Evitar duplicar una vacante ingresada manualmente
El sistema SHALL reutilizar una publicación existente que tenga la misma URL pública canónica, sin importar si se encontró por una fuente automática o por el registro manual.

#### Scenario: La URL ya está registrada
- **WHEN** la persona administradora registra una vacante cuya URL canónica ya existe
- **THEN** el sistema actualiza o reutiliza la publicación existente y no crea un segundo registro global

#### Scenario: Se vuelve a registrar una vacante sin cambios materiales
- **WHEN** una vacante existente se registra manualmente de nuevo para un perfil ya analizado
- **THEN** el sistema reutiliza el análisis completado para el perfil sin reevaluarlo
