# Spec Delta

## ADDED Requirements

### Requirement: Preseleccionar vacantes automáticas por título
El sistema SHALL clasificar en lote los títulos de resultados automáticos frente a los términos compartidos de la solicitud de búsqueda, descartando únicamente incompatibilidades laborales claras.

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

## MODIFIED Requirements

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

### Requirement: Permitir una actualización manual de fuentes
El sistema SHALL permitir a la persona administradora iniciar una actualización de fuentes antes del siguiente ciclo periódico, usando el flujo de búsqueda, preselección conservadora por título, deduplicación y análisis elegible.

#### Scenario: Administración inicia una actualización antes del horario
- **WHEN** la persona administradora solicita actualizar fuentes antes de que venza el intervalo automático de 120 minutos
- **THEN** el sistema encola la actualización inmediatamente sin esperar al siguiente ciclo y conserva el horario periódico configurado

#### Scenario: Una búsqueda encuentra una vacante nueva elegible
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
