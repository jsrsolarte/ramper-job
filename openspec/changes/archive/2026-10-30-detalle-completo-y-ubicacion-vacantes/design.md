# Design

## Context

El conector actual recorre las combinaciones de búsqueda y obtiene los datos de las tarjetas o del JSON-LD de la lista. El contrato común `JobListing` ya incluye salario, ubicación, descripción y contrato; el modelo `Vacancy` además conserva `raw_data` como JSON. El análisis se agenda por vacante y actualmente puede alcanzar todos los perfiles activos, por lo que una vacante recopilada para una ciudad puede acabar evaluándose para otro perfil.

La ficha de Elempleo presenta un resumen superior y una descripción del cargo con rótulos como «Salario», «Tipo de contrato», «Lugar», «Experiencia» y «Condiciones». En el ejemplo compartido, la ficha aclara que el rango del listado es `$4 a $4,5 millones`, el salario exacto es `$4.214.000 pagos mensuales` y el lugar es Bogotá, Av. 68 # 13-50, presencial.

## Goals / Non-Goals

**Goals:**
- Consultar cada ficha única una sola vez por actualización y extraer sus campos publicados.
- Conservar texto original y valores por separado para que el análisis y la interfaz no pierdan precisión.
- Filtrar por ubicación para cada perfil sin descartar del catálogo global una vacante válida para otra persona.
- Evitar que las fichas inaccesibles interrumpan una búsqueda completa.

**Non-Goals:**
- Usar cuentas de Elempleo, automatizar postulaciones o evadir bloqueos y límites del sitio.
- Geocodificar direcciones, inferir una ciudad por la ruta de búsqueda o corregir los datos publicados.
- Convertir expresiones salariales ambiguas en cifras exactas.

## Decisions

### Consultar la ficha y combinar fuentes

Después de consolidar los resultados de todas las búsquedas por identidad de vacante, el conector consultará una vez cada URL única de publicación. Usará JSON-LD y los campos visibles para identificar las condiciones. Para la descripción dará prioridad al bloque visible del cargo y usará JSON-LD como respaldo, porque algunas fichas publican ahí solo el texto «COP». Así evita repetir solicitudes cuando una oferta aparece en varias consultas y recoge datos que no existen en la tarjeta.

El parser conservará el texto original de la descripción y los valores visibles. Para salario mantendrá separados el rango mostrado en el listado, el valor o texto salarial de la ficha y la periodicidad explícita. No calculará valores numéricos si el formato no es inequívoco.

### Mantener compatibilidad y datos estructurados

Los valores principales se proyectarán en los campos existentes (`salary`, `location`, `contract_type`, `description`) para que las fuentes y vistas actuales sigan funcionando. El detalle completo se guardará como un objeto versionado dentro de `raw_data`, por ejemplo `raw_data.details`, con claves para salario, ciudad, dirección, modalidad, contrato, nivel educativo, experiencia, área, horario, responsabilidades, requisitos y cantidad de vacantes. Cada clave podrá quedar vacía si la ficha no la publica. Esto evita una migración solo para datos específicos de una fuente y deja el esquema disponible para otros conectores.

### Aplicar ubicación por perfil

Las vacantes enriquecidas permanecerán en el catálogo común. Antes de crear o mostrar un análisis, el sistema comparará la ciudad real de la ficha con las ubicaciones expandidas del perfil. Un empleo presencial en Bogotá no pasa a un perfil de Medellín/Envigado, aunque se haya encontrado al consultar una ruta local. El trabajo remoto depende de `remote_ok`. Si la ubicación sigue desconocida, se conserva como desconocida; con ubicaciones explícitas y sin aceptación remota no se recomienda hasta poder confirmar compatibilidad.

El filtrado será por perfil: no se eliminarán publicaciones globales porque una familia tenga preferencias distintas. También se ocultarán análisis existentes cuyo detalle actualizado contradiga la ubicación del perfil. Cuando cambie la descripción o un campo material de la ficha, se volverá a programar el análisis; una consulta que no cambie los datos no generará otra llamada a IA.

### Mantener una extracción tolerante

La consulta de cada ficha usará la misma sesión, un intervalo entre solicitudes y un timeout acotado. Un error o cambio de estructura en una ficha conservará los datos ya obtenidos en la lista y seguirá con la siguiente. Los datos de detalle solo reemplazarán valores normalizados cuando la ficha sí proporcione un valor; los datos ausentes no borrarán valores existentes.

### Mostrar datos y palabras clave de forma compacta

El dashboard resaltará ciudad, modalidad, dirección/zona, salario y contrato; mostrará formación, experiencia y horario cuando existan. La descripción completa seguirá guardada como evidencia y el análisis de IA conservará las categorías organizadas en la base de datos. La tarjeta mostrará solo hasta cinco palabras clave breves tomadas de la descripción; los detalles de coincidencia quedarán plegados.

## Risks / Trade-offs

- [Cada vacante requiere una solicitud pública adicional y el refresco tardará más] → Consolidar por identidad antes de visitar fichas, aplicar un intervalo breve y límites de tiempo por página.
- [Elempleo puede cambiar sus rótulos o estructura HTML] → Priorizar JSON-LD cuando sea completo, añadir fixtures de la ficha visible y tratar fallos por vacante, no por lote.
- [Los nombres de ciudad pueden ser parciales o ambiguos] → Comparar nombres normalizados con los grupos de cercanía existentes; no usar geocodificación ni inferir la ciudad desde la consulta.
- [Una ubicación desconocida puede reducir el número de recomendaciones] → Conservar la vacante y mostrar que el dato falta, sin presentarla como compatible cuando no se puede comprobar la preferencia.
- [La relectura de detalles puede producir nuevos análisis y consumo de OmniRoute] → Reanalizar solo cuando cambie el contenido material usado por el análisis.

## Migration Plan

No se requiere una migración de esquema: los campos principales ya existen y el objeto `raw_data` permite guardar los detalles nuevos. En el siguiente refresco se enriquecerán las vacantes y se reanalizarán solo las que tengan datos materiales distintos. Para revertir el cambio, se puede volver al parser anterior y dejar los objetos `raw_data.details` sin usar; no es necesario borrar datos ni restaurar la base.
