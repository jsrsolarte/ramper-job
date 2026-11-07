# Proposal

## Why

La búsqueda actual toma los datos principalmente de las tarjetas de resultados y por eso deja campos importantes vacíos o ambiguos. La ficha de Elempleo contiene salario detallado, ciudad y dirección, modalidad, contrato, experiencia, formación y condiciones; además, puede revelar que una oferta encontrada al buscar Medellín realmente está en Bogotá.

## What Changes

- Visitar la ficha pública de cada vacante única y extraer sus datos visibles, además de los disponibles en JSON-LD.
- Normalizar salario, ubicación y tipo de contrato en los campos existentes, y conservar los demás datos de la ficha en una estructura organizada.
- Comprobar la ubicación real de la ficha contra las ubicaciones preferidas expandidas; descartar las ofertas presenciales que indiquen claramente una ciudad fuera del área aceptada.
- Permitir vacantes remotas según la preferencia del perfil y conservar como desconocida una ubicación que la fuente no permita determinar.
- Guardar en la base de datos la descripción original y las categorías organizadas por IA, incluidas palabras clave breves.
- Mostrar en el dashboard los datos estructurados y solo las palabras clave de la descripción; mantener plegados los detalles de coincidencia.
- Mantener los datos del listado cuando una ficha individual no responda, sin detener la consulta completa de Elempleo.

## Capabilities

### New Capabilities
- `ingesta-vacantes`: extracción de datos completos desde las fichas públicas de Elempleo, normalización y validación geográfica antes del análisis.

### Modified Capabilities

## Impact

El cambio afecta el conector de Elempleo, la normalización y persistencia de vacantes, el flujo de actualización, la presentación de resultados y las pruebas del conector. Se limita a páginas públicas; no usa cuentas, no evade controles de acceso y no modifica la descripción original publicada.
