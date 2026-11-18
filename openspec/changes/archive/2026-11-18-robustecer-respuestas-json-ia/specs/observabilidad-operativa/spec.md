# Spec Delta

## ADDED Requirements

### Requirement: Medir recuperación de formato de IA
El sistema SHALL registrar por etapa los resultados de normalización y reparación de formato y los recursos reportados por cada llamada, sin guardar contenido privado ni respuestas completas.

#### Scenario: Se normaliza un bloque Markdown
- **WHEN** una respuesta delimitada se interpreta sin llamada adicional
- **THEN** las métricas distinguen esa normalización de una reparación mediante IA

#### Scenario: Se solicita reparación
- **WHEN** se realiza la llamada de reparación
- **THEN** se registran su resultado, duración y tokens disponibles de forma separada de la evaluación original

#### Scenario: Diagnóstico sin contenido privado
- **WHEN** falla la interpretación o reparación
- **THEN** los registros y métricas contienen solo categorías controladas y metadatos técnicos seguros, sin prompts, CV, vacante ni fragmentos de respuesta
