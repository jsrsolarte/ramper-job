# Diagnósticos de formato del análisis de IA

Los intentos de puntuación usan `AICallAttempt.error_category` para guardar únicamente códigos controlados. El panel administrativo traduce esos códigos a etiquetas y agrupa los conteos por periodo. Los registros antiguos `analysis_invalid` se muestran como formato inválido histórico.

## Códigos

- `omniroute.invalid_json`: OmniRoute o el contenido del modelo no se pudo interpretar como JSON.
- `analysis.schema.not_object`: el JSON no contiene un objeto en la raíz.
- `analysis.rubric.version`: la versión declarada no coincide con la rúbrica solicitada.
- `analysis.rubric.criteria_set`: faltan o sobran criterios en el desglose.
- `analysis.rubric.<criterio>.<regla>`: rechazo de un criterio. Los criterios permitidos son `skills`, `experience`, `alignment`, `education` y `profile_criteria`; las reglas permitidas son `not_object`, `score_not_numeric`, `score_out_of_range`, `score_precision`, `status_invalid`, `evidence_invalid`, `status_score_mismatch` y `evidence_required`.
- `analysis.rubric.critical_requirements.not_list` y `analysis.rubric.critical_requirement.<regla>`: estructura o contenido de requisitos críticos; las reglas permitidas son `not_object`, `text_invalid`, `status_invalid`, `evidence_invalid` y `evidence_required`.
- `analysis.rubric.reasons.not_string_list` y `analysis.rubric.gaps.not_string_list`: lista de razones o brechas con estructura inválida.
- `analysis_invalid`: categoría genérica conservada para datos históricos o errores de validación no clasificados.

Los códigos nunca contienen texto de la solicitud, del CV, del perfil o de la respuesta del modelo. El mensaje asociado al análisis sigue siendo genérico.
