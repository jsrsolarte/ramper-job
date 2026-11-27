# Design

## Context

Ver `proposal.md` para la motivación y `specs/evidencia-cv-reutilizable/spec.md` para el contrato. `profiles.extract` extrae texto plano de PDF y DOCX y limita la salida a 30.000 caracteres. `matching.services.get_profile_search_terms` ya conserva palabras clave por revisión y configuración, pero `matching.tasks` vuelve a extraer y enviar el texto completo del CV para cada puntuación. Las llamadas de IA ya registran tokens reportados por OmniRoute.

## Goals / Non-Goals

**Goals:**

- Pagar la lectura del CV completo una vez por revisión y versión de extracción.
- Reutilizar evidencia compacta para términos de búsqueda y puntuaciones de vacantes.
- Seleccionar evidencia por vacante sin confundir «no seleccionada» con «no existe en el CV».
- Medir ahorro de tokens y conservar resultados verificables contra el CV fuente.

**Non-Goals:**

- Cambiar la rúbrica, los criterios de elegibilidad o el puntaje final.
- Añadir OCR para CV escaneados ni ampliar los formatos aceptados.
- Compartir hechos extraídos entre perfiles.

## Decisions

### Conservar hechos laborales discretos con su origen

Guardar una representación estructurada por `ProfileRevision` y versión del extractor. Cada hecho contiene un resumen conciso, categoría —experiencia, habilidad, logro, educación o certificación—, etiquetas normalizadas útiles para recuperación y un fragmento de origen que permita comprobarlo. Conservar fechas, alcance y métricas cuando estén disponibles. Excluir contacto, datos personales ajenos al trabajo y texto de formato.

La clave por revisión evita mezclar un CV nuevo con análisis antiguos; la versión del extractor permite recalcular solo cuando cambie el esquema de extracción. El acceso queda limitado al perfil dueño, como el CV fuente.

Alternativa considerada: persistir un único resumen en prosa. Se descarta porque dificulta elegir evidencia por criterio, rastrear una afirmación a su origen y conservar fechas o logros separados.

### Crear la representación junto con la primera generación de términos

Cuando una revisión no tenga representación, usar una sola llamada que lea el texto completo y produzca tanto los hechos estructurados como las palabras clave sugeridas. Guardar ambos resultados asociados a sus versiones respectivas. Si luego cambia el prompt de búsqueda, derivar nuevos términos desde la representación compacta sin volver a enviar el CV completo. Si falla la extracción, dejar el trabajo pendiente para el flujo de reintentos y no usar otra revisión como sustituto.

Para revisiones existentes, generar la representación de forma diferida cuando la búsqueda o el análisis la necesiten; no requiere una migración masiva de CV ni procesar perfiles que ya no estén activos.

### Recuperar hechos por vacante con cobertura por rúbrica

Construir la consulta de recuperación desde el cargo, responsabilidades y requisitos de la vacante. Compararla con el vocabulario normalizado de los hechos y priorizar candidatos por criterio de rúbrica: habilidades, experiencia, alineación, educación y otros criterios explícitos. Los sinónimos laborales normalizados en la extracción ayudan a encontrar equivalencias que no compartan la misma frase literal. Conservar siempre hechos pertinentes a requisitos obligatorios, incluidos fechas, credenciales o evidencia que pueda contradecirlos.

Antes de puntuar, revisar la cobertura de cada criterio que aplique a la vacante. Si un criterio tiene requisitos explícitos pero la selección no aporta contexto suficiente, ampliar el conjunto con más hechos de esa categoría o con la representación compacta completa. La ausencia de un hecho en la selección inicial no se interpreta por sí sola como ausencia en el CV.

Alternativa considerada: enviar siempre toda la representación compacta al modelo de puntuación. Se descarta como camino principal porque mantiene hechos irrelevantes para muchas vacantes; queda como ampliación de cobertura cuando la selección específica no baste.

### Mantener intacto el flujo posterior de puntuación

El modelo de puntuación recibe hechos seleccionados, preferencias vigentes y publicación; continúa devolviendo la rúbrica versionada actual. La etapa de organización de la vacante permanece separada y no recibe evidencia del perfil. Los análisis históricos siguen ligados a su `ProfileRevision` y configuración original.

### Verificar ahorro sin ocultar pérdida de evidencia

Comparar tokens de entrada reportados para una muestra representativa de CV y vacantes antes y después. Revisar además que los hechos que sostienen cada criterio en resultados anteriores sigan presentes en el conjunto enviado y que la respuesta mantenga la estructura válida. No fijar el éxito solo por un resumen de menor tamaño: la selección debe conservar evidencia de credenciales, requisitos obligatorios y contradicciones explícitas.

## Risks / Trade-offs

- [La extracción puede omitir o deformar un hecho relevante] → Guardar fragmentos de origen, validar el esquema y permitir ampliación a más hechos compactos si un criterio no queda cubierto.
- [La recuperación por términos puede no reconocer una equivalencia semántica] → Normalizar habilidades y funciones durante la extracción y favorecer cobertura alta, no un corte estrecho por puntaje.
- [La extracción inicial añade costo a revisiones antiguas] → Combinarla con la generación inicial de términos y crearla bajo demanda solo una vez por revisión.
- [Una respuesta de extracción puede incluir información personal innecesaria] → Limitar el esquema a hechos laborales y validar que los campos y textos guardados no conserven datos de contacto o atributos personales ajenos al cargo.

## Migration Plan

Crear almacenamiento versionado de evidencia sin modificar ni borrar los CV ni las revisiones existentes. Generar evidencia de forma diferida en el siguiente procesamiento de cada revisión activa. Durante la transición, un análisis solo usa una representación ya válida para su revisión; si falta o falla, se mantiene pendiente para reintento. La reversión puede desactivar el uso de la nueva representación y volver al flujo anterior, conservando los archivos y los resultados históricos.
