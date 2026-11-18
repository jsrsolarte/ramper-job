# Diagnósticos de formato del análisis de IA

Los intentos de puntuación usan `AICallAttempt.error_category` para guardar únicamente códigos controlados. El panel administrativo traduce esos códigos a etiquetas y agrupa los conteos por periodo. Los registros antiguos `analysis_invalid` se muestran como formato inválido histórico.

## Normalización y reparación

El cliente acepta un objeto JSON directo o un único bloque Markdown completo con objeto JSON y sin texto externo. Los bloques ambiguos, múltiples, incompletos, sobredimensionados y los valores raíz que no son objetos se rechazan sin extraer fragmentos. La normalización local no genera otra llamada.

Si el objeto directo o el interior de un único bloque sigue teniendo sintaxis inválida, se permite una sola llamada de reparación. Esa solicitud contiene solamente la respuesta original y el esquema requerido; no vuelve a enviar el perfil, CV, vacante ni prompt de evaluación por separado. El contenido se trata como dato no confiable. La respuesta reparada solo se acepta si puede demostrarse que equivale a una corrección sintáctica conservadora y pasa después el validador de la etapa. JSON válido con errores de rúbrica u organización no se repara.

`AICallAttempt.format_action` distingue `direct`, `normalized`, `repair_requested` y `repair_succeeded`. Las etapas `scoring_repair` y `organization_repair` tienen su propia duración, resultado y tokens reportados. Los tokens quedan nulos cuando OmniRoute no los informa. Los paneles agregan estos datos por periodo y etapa; el historial existente queda clasificado como JSON directo por defecto.

Los registros, mensajes de error y métricas no guardan prompts, respuestas, CV, datos de vacantes ni fragmentos de contenido. Solo persisten códigos de categoría permitidos, etapa, resultado, duración, uso de tokens disponible y la acción de formato. El texto de la respuesta existe únicamente en memoria durante la llamada a la ruta configurada de OmniRoute.

## Códigos

- `omniroute.invalid_json`: OmniRoute o el contenido del modelo no se pudo interpretar como JSON.
- `omniroute.ambiguous_content`: el contenido delimitado no es un único bloque inequívoco.
- `omniroute.repair_not_preserved`: no se pudo demostrar que la reparación conserva todos los valores y su estructura.
- `omniroute.repair_invalid`: la respuesta de reparación no contiene un objeto JSON interpretable.
- `omniroute.structured_output_unsupported`: la ruta rechazó explícitamente el formato estructurado; se permite una única solicitud compatible alternativa.
- `analysis.schema.not_object`: el JSON no contiene un objeto en la raíz.
- `analysis.rubric.version`: la versión declarada no coincide con la rúbrica solicitada.
- `analysis.rubric.criteria_set`: faltan o sobran criterios en el desglose.
- `analysis.rubric.<criterio>.<regla>`: rechazo de un criterio. Los criterios permitidos son `skills`, `experience`, `alignment`, `education` y `profile_criteria`; las reglas permitidas son `not_object`, `score_not_numeric`, `score_out_of_range`, `score_precision`, `status_invalid`, `evidence_invalid`, `status_score_mismatch` y `evidence_required`.
- `analysis.rubric.critical_requirements.not_list` y `analysis.rubric.critical_requirement.<regla>`: estructura o contenido de requisitos críticos; las reglas permitidas son `not_object`, `text_invalid`, `status_invalid`, `evidence_invalid` y `evidence_required`.
- `analysis.rubric.reasons.not_string_list` y `analysis.rubric.gaps.not_string_list`: lista de razones o brechas con estructura inválida.
- `analysis_invalid`: categoría genérica conservada para datos históricos o errores de validación no clasificados.

Los códigos nunca contienen texto de la solicitud, del CV, del perfil o de la respuesta del modelo. El mensaje asociado al análisis sigue siendo genérico.
