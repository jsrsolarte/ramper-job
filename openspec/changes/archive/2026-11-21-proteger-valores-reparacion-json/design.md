# Design

## Context

`matching/json_response.py` utiliza sustituciones globales para reconstruir sintaxis antes de comparar valores. Una sustitución puede actuar dentro de una cadena, de modo que la comparación posterior valida un valor ya modificado. La normalización de bloques Markdown y la llamada de reparación tienen contratos existentes.

## Goals / Non-Goals

**Goals:** asegurar que las transformaciones de sintaxis nunca toquen literales y rechazar equivalencias ambiguas.

**Non-Goals:** modificar rúbrica, proveedor, política de reintentos, datos históricos o aceptar nuevas clases de JSON ambiguo.

## Decisions

- Sustituir las expresiones regulares globales por una comprobación consciente de cadenas y escapes, o rechazar conservadoramente los casos que no pueda verificar. Las correcciones permitidas actúan exclusivamente fuera de literales; después se comparan recursivamente claves, tipos y valores. Mantener la detección de claves duplicadas.
- Conservar el límite de una llamada de reparación y los validadores existentes. El fallo conserva la categoría segura y el flujo durable sin registrar contenidos.
- Verificar con pruebas unitarias y de integración sintéticas el caso reproducido, las correcciones válidas, comillas y barras escapadas, Unicode, estructuras anidadas, claves duplicadas y cambios de tipos. Las pruebas deben comprobar que no se persiste un resultado alterado.

## Risks / Trade-offs

- [Un JSON malformado es ambiguo] → rechazar cuando no se pueda demostrar equivalencia, aunque aumenten los reintentos.
- [Regresión en recuperación válida] → cubrir explícitamente coma final y separadores faltantes externos a cadenas, además del flujo Markdown existente.

## Migration Plan

Implementar y validar con datos sintéticos; probar en staging y revisar resultados. Promover a producción solo con autorización explícita, mediante el flujo Git/Flux. Revertir a la imagen anterior si hay regresiones; no modificar resultados históricos como parte de este cambio.
