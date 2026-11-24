# Proposal

## Why

Hoy el texto extraído del CV puede llegar hasta 30.000 caracteres y se envía de nuevo al modelo para cada análisis de vacante. Una representación laboral compacta, fiel al documento y reutilizable por revisión puede reducir el consumo repetido de tokens y limitar la información irrelevante enviada en cada evaluación.

## What Changes

- Extraer y conservar por revisión del perfil una representación compacta de evidencia laboral respaldada por el CV.
- Reutilizarla para sugerir términos de búsqueda y para analizar vacantes, seleccionando para cada vacante la evidencia que corresponda a sus requisitos y responsabilidades.
- Evitar que el contenido irrelevante para la evaluación —como formato y datos de contacto— se envíe repetidamente al modelo.
- Regenerar la representación cuando cambie el CV y preservarla separada por persona y revisión.

## Capabilities

### New Capabilities

- `evidencia-cv-reutilizable`: Extracción, almacenamiento y selección de evidencia laboral compacta para personalizar búsquedas y análisis.

### Modified Capabilities

Ninguna.

## Impact

- Afecta la extracción en `profiles`, la generación de términos en `matching.services` y el análisis por vacante en `matching.tasks`.
- Cambia el contenido enviado a OmniRoute: una extracción inicial por revisión y evidencia acotada en las llamadas posteriores.
- Requiere versionar la representación, mantener su trazabilidad con el CV de origen y medir el ahorro de tokens sin perder evidencia necesaria para la rúbrica.
