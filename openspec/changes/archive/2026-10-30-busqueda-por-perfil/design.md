# Design

## Context

Las búsquedas periódicas usan hoy un único `ELEMPLEO_SEARCH_URL` general y un conector sin parámetros. Los perfiles ya conservan revisiones de CV y criterios; la aplicación extrae el texto de cada CV, tiene un adaptador a OmniRoute y mantiene configuraciones de análisis inmutables. Elempleo expone rutas públicas de búsqueda por término, como `/co/ofertas-empleo/trabajo-procesos`.

## Goals / Non-Goals

**Goals:**
- Generar búsquedas pertinentes por perfil y revisión sin invocar OmniRoute en cada ciclo periódico.
- Reutilizar la configuración versionada de IA y permitir ajustar el prompt desde Django Admin.
- Pasar términos al contrato de los conectores, consultar Elempleo por términos y deduplicar la unión de resultados.
- Mantener una vacante compartida por URL de fuente y análisis independiente por cada perfil.

**Non-Goals:**
- Automatizar postulación, iniciar sesión en Elempleo o evadir bloqueos y límites de acceso.
- Añadir una interfaz para editar manualmente las palabras clave en este cambio.
- Cambiar el prompt o los parámetros que califican una vacante después de encontrarla.

## Decisions

### Ampliar la configuración versionada de MatchingConfig

Agregar un campo `search_prompt` a la configuración ya versionada y editable en Admin. Cada configuración nueva copia la configuración vigente antes de aplicar cambios, siguiendo el patrón existente; la primera versión recibe un prompt predeterminado para producir un JSON de entre tres y cinco términos laborales. Así la persona administradora puede afinar la búsqueda sin desplegar código y cada conjunto generado puede identificar su configuración. Se descarta crear un segundo panel de versiones independiente.

### Persistir el conjunto de términos por revisión y configuración

Guardar el JSON validado de términos en un registro asociado a `ProfileRevision` y `MatchingConfig`, con unicidad para ese par. El sistema genera el conjunto cuando falta y lo reutiliza en actualizaciones posteriores. Un CV o criterio actualizado crea una nueva revisión; un prompt de búsqueda actualizado crea una configuración nueva y por tanto un conjunto nuevo. Se evita regenerar palabras en cada intervalo de 180 minutos y se conserva la trazabilidad.

### Generar términos a partir del texto ya extraído

La tarea obtiene el texto de la revisión de perfil con `extract_revision_text` y envía al endpoint OmniRoute el CV, los criterios y el `search_prompt` activo. El adaptador exige un objeto JSON con lista acotada de cadenas únicas, elimina valores vacíos y rechaza respuestas malformadas. Si OmniRoute falla, deja pendiente la búsqueda de ese perfil, conserva las vacantes y resultados previos y reintenta sin sustituir los términos por una consulta general.

### Extender el contrato de los conectores con términos

El contrato común recibirá una lista de palabras clave. Elempleo construirá una ruta pública por término, con el prefijo observado `trabajo-` y el término normalizado como slug; extraerá y combinará sus páginas con una pausa corta entre solicitudes y deduplicará por URL. Los errores de una consulta no deben invalidar resultados ya obtenidos de otros términos; se registrará el estado del conjunto de consultas. Se descartan selectores basados solo en texto completo del CV, que producirían URLs grandes y búsquedas demasiado amplias.

### Encolar análisis después de unir las vacantes

La actualización programada recorrerá perfiles activos con CV, resolverá su conjunto de términos y consultará los conectores. Guardará las vacantes mediante la unicidad existente por fuente y URL; las publicaciones nuevas pasarán al flujo existente que genera análisis separados para cada perfil. Una publicación hallada por un familiar puede ser útil a otro, pero su puntaje y motivos siguen aislados por cuenta.

## Risks / Trade-offs

- [Elempleo puede cambiar el formato de las rutas de búsqueda] → Mantener el constructor de URL dentro del conector y cubrir el slug, las páginas sin resultados y el manejo de bloqueos con fixtures.
- [El modelo puede proponer términos redundantes o poco útiles] → Acotar la lista, validar duplicados y conservar el prompt en Admin para su ajuste.
- [Una actualización podría generar varias peticiones por perfil] → Limitar el número de términos y espaciar consultas; no seguir enlaces de autenticación ni reintentar respuestas 401, 403 o 429.
- [Un cambio de prompt invalida cachés de términos] → La configuración versionada forma parte de la clave única, así los términos anteriores permanecen asociados a su versión y no se sobrescriben.

## Migration Plan

Agregar el prompt con valor predeterminado a las nuevas versiones de configuración y una tabla para los conjuntos de términos por revisión/configuración. Los registros existentes quedan intactos; la próxima tarea programada generará términos para los perfiles actuales. Para revertir, detener las tareas de búsqueda por perfil y volver a usar el conector general, preservando vacantes y análisis existentes.
